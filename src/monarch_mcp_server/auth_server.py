"""
Local HTTP server for browser-based Monarch Money authentication.

When the MCP server starts and no authentication token is found,
this module spins up a temporary local web server, opens the user's
browser to a login page, and saves the resulting token to the system
keyring once the user authenticates.
"""

import asyncio
from dataclasses import dataclass
import json
import logging
import os
import socket
import threading
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

from gql.transport.exceptions import TransportServerError
from monarchmoney import MonarchMoney, RequireMFAException, LoginFailedException

from monarch_mcp_server.secure_session import secure_session, is_auth_error

logger = logging.getLogger(__name__)

# Maximum time (seconds) the auth server will stay alive waiting for login
_AUTH_TIMEOUT = 600  # 10 minutes

# Guard: prevent multiple auth servers from running simultaneously
_auth_lock = threading.Lock()
_auth_guard: dict[str, bool] = {"active": False}

# ── HTML served to the browser ──────────────────────────────────────────

_LOGIN_PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Monarch Money - Sign In</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
background:#f5f5f5;display:flex;justify-content:center;align-items:center;
min-height:100vh}
.card{background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.1);
padding:40px;width:400px;max-width:92vw}
h1{color:#1a1a2e;font-size:22px;margin-bottom:6px}
.sub{color:#666;font-size:14px;margin-bottom:24px}
.fg{margin-bottom:16px}
label{display:block;color:#333;font-size:14px;font-weight:500;margin-bottom:5px}
input{width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:8px;
font-size:14px;outline:none;transition:border-color .2s}
input:focus{border-color:#4a90d9}
button{width:100%;padding:12px;background:#4a90d9;color:#fff;border:none;
border-radius:8px;font-size:15px;font-weight:500;cursor:pointer;
transition:background .2s}
button:hover{background:#357abd}
button:disabled{background:#bbb;cursor:not-allowed}
.err{color:#e74c3c;font-size:13px;margin-top:12px;display:none}
.ok{text-align:center}
.ok h2{color:#27ae60;margin-bottom:10px}
.ok p{color:#666}
#mfa{display:none}
#done{display:none}
.sp{display:inline-block;width:15px;height:15px;border:2px solid #fff;
border-top-color:transparent;border-radius:50%;animation:r .7s linear infinite;
margin-right:8px;vertical-align:middle}
@keyframes r{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div class="card">

  <div id="login">
    <h1>Monarch Money</h1>
    <p class="sub">Sign in to connect your MCP server</p>
    <div class="fg">
      <label for="email">Email</label>
      <input id="email" type="email" placeholder="you@example.com" autofocus>
    </div>
    <div class="fg">
      <label for="pw">Password</label>
      <input id="pw" type="password" placeholder="Your password">
    </div>
    <button id="lbtn" onclick="doLogin()">Sign In</button>
    <div id="lerr" class="err"></div>
  </div>

  <div id="mfa">
    <h1>Two-Factor Authentication</h1>
    <p class="sub">Enter the code from your authenticator app</p>
    <div class="fg">
      <label for="code">Authentication Code</label>
      <input id="code" type="text" placeholder="123456" maxlength="10" inputmode="numeric">
    </div>
    <button id="mbtn" onclick="doMFA()">Verify</button>
    <div id="merr" class="err"></div>
  </div>

  <div id="done" class="ok">
    <h2>Authentication Successful</h2>
    <p>Your MCP server is now connected to Monarch Money.</p>
    <p style="margin-top:10px;font-size:13px;color:#999">You can close this tab.</p>
  </div>

</div>
<script>
function show(id){
  ['login','mfa','done'].forEach(s=>document.getElementById(s).style.display='none');
  document.getElementById(id).style.display='block';
  const af=document.querySelector('#'+id+' input');
  if(af) af.focus();
}
function showErr(id,msg){const e=document.getElementById(id);e.textContent=msg;e.style.display='block'}
function hideErr(id){document.getElementById(id).style.display='none'}

async function doLogin(){
  const email=document.getElementById('email').value.trim();
  const pw=document.getElementById('pw').value;
  if(!email||!pw){showErr('lerr','Please enter both email and password.');return}
  const btn=document.getElementById('lbtn');
  btn.disabled=true;btn.innerHTML='<span class="sp"></span>Signing in\u2026';
  hideErr('lerr');
  try{
    const r=await fetch('/login',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({email:email,password:pw})});
    const d=await r.json();
    if(d.success){show('done')}
    else if(d.mfa_required){show('mfa')}
    else if(d.error){showErr('lerr',d.error)}
  }catch(e){showErr('lerr','Connection error. Please try again.')}
  btn.disabled=false;btn.innerHTML='Sign In';
}

async function doMFA(){
  const code=document.getElementById('code').value.trim();
  if(!code){showErr('merr','Please enter your authentication code.');return}
  const btn=document.getElementById('mbtn');
  btn.disabled=true;btn.innerHTML='<span class="sp"></span>Verifying\u2026';
  hideErr('merr');
  try{
    const r=await fetch('/mfa',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({code:code})});
    const d=await r.json();
    if(d.success){show('done')}
    else if(d.error){showErr('merr',d.error)}
  }catch(e){showErr('merr','Connection error. Please try again.')}
  btn.disabled=false;btn.innerHTML='Verify';
}

document.getElementById('email').addEventListener('keydown',e=>{if(e.key==='Enter'){
  document.getElementById('pw').focus()}});
document.getElementById('pw').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin()});
document.getElementById('code').addEventListener('keydown',e=>{if(e.key==='Enter')doMFA()});
</script>
</body>
</html>
"""


# ── Helpers ─────────────────────────────────────────────────────────────

def _find_free_port() -> int:
    """Find an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _run_sync(coro):
    """Run an async coroutine synchronously in a one-shot event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Request handler ─────────────────────────────────────────────────────

@dataclass
class _AuthState:
    """Mutable state shared between handler and server loop."""
    email: str = ""
    password: str = ""
    awaiting_mfa: bool = False
    completed: bool = False


class _AuthHandler(BaseHTTPRequestHandler):
    """HTTP handler that serves the login page and processes auth requests."""

    # Attached by the factory before the server starts
    auth_state: _AuthState

    # ── GET ──

    def do_GET(self):  # pylint: disable=invalid-name
        """Serve the login page for GET /."""
        if self.path == "/":
            self._send_html(_LOGIN_PAGE)
        else:
            self.send_error(404)

    # ── POST ──

    def do_POST(self):  # pylint: disable=invalid-name
        """Handle POST requests for /login and /mfa."""
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            data = json.loads(body) if body else {}
        except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
            self._send_json({"error": "Invalid request body"})
            return

        if self.path == "/login":
            self._handle_login(data)
        elif self.path == "/mfa":
            self._handle_mfa(data)
        else:
            self.send_error(404)

    # ── Auth logic ──

    def _handle_login(self, data: dict):
        """Authenticate with email/password, handling MFA if required."""
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not email or not password:
            self._send_json({"error": "Email and password are required."})
            return

        try:
            mm = MonarchMoney()
            _run_sync(mm.login(email, password, use_saved_session=False, save_session=False))

            # Login succeeded without MFA
            secure_session.save_authenticated_session(mm)
            self.auth_state.completed = True
            logger.info("Browser authentication successful (no MFA)")
            self._send_json({"success": True})

        except RequireMFAException:
            self.auth_state.email = email
            self.auth_state.password = password
            self.auth_state.awaiting_mfa = True
            self._send_json({"mfa_required": True})

        except LoginFailedException:
            logger.error("Login failed for %s: invalid credentials", email)
            self._send_json({"error": "Invalid email or password."})

        except TransportServerError as exc:
            code = getattr(exc, "code", "unknown")
            logger.error("Monarch API HTTP %s during login: %s", code, exc)
            self._send_json(
                {"error": f"Monarch API error (HTTP {code}). Please try again later."}
            )

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Unexpected error during login: %s", exc)
            self._send_json({"error": f"Login failed: {exc}"})

    def _handle_mfa(self, data: dict):
        """Verify the MFA code and complete authentication."""
        code = data.get("code", "").strip()

        if not code:
            self._send_json({"error": "Authentication code is required."})
            return

        if not self.auth_state.awaiting_mfa:
            self._send_json({"error": "No pending MFA challenge. Please sign in again."})
            return

        try:
            mm = MonarchMoney()
            _run_sync(
                mm.multi_factor_authenticate(
                    self.auth_state.email,
                    self.auth_state.password,
                    code,
                )
            )

            secure_session.save_authenticated_session(mm)
            self.auth_state.completed = True
            logger.info("Browser authentication successful (with MFA)")
            self._send_json({"success": True})

        except LoginFailedException:
            logger.error("MFA verification failed: invalid code")
            self._send_json({"error": "Invalid authentication code. Please try again."})

        except TransportServerError as exc:
            code_ = getattr(exc, "code", "unknown")
            logger.error("Monarch API HTTP %s during MFA: %s", code_, exc)
            self._send_json(
                {"error": f"Monarch API error (HTTP {code_}). Please try again later."}
            )

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Unexpected error during MFA: %s", exc)
            self._send_json({"error": f"MFA verification failed: {exc}"})

    # ── Response helpers ──

    def _send_json(self, obj: dict):
        """Send a JSON response with 200 status."""
        payload = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_html(self, html: str):
        """Send an HTML response with 200 status."""
        payload = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):  # pylint: disable=redefined-builtin
        """Redirect default stderr logging to our logger."""
        logger.debug("Auth server: %s", format % args)


# ── Public API ──────────────────────────────────────────────────────────

def _validate_token(token: str) -> bool | None:
    """Check whether a stored token is still valid by making a quick API call.

    Returns True if the token works, False if the token is definitively
    invalid (401/403), or None if validation was inconclusive due to a
    server-side error (so the existing token should be kept).
    """
    try:
        mm = MonarchMoney(token=token)
        _run_sync(mm.get_accounts())
        return True
    except Exception as exc:  # pylint: disable=broad-exception-caught
        if is_auth_error(exc):
            logger.warning("Stored token is invalid or expired: %s", exc)
            return False
        # Server-side error (5xx, network, etc.) — don't discard the token
        logger.warning("Could not validate token (server error): %s", exc)
        return None


def trigger_auth_flow() -> None:
    """Check for existing credentials; if absent, open a browser login page.

    This is non-blocking: a daemon thread runs the temporary HTTP server
    while the MCP server continues its normal startup.  The auth server
    shuts itself down once the user completes login or after a timeout.

    Safe to call multiple times — only one auth server will run at a time.
    """
    with _auth_lock:
        if _auth_guard["active"]:
            logger.info("Auth server already running — skipping")
            return

        # Check keyring token — validate it's still usable
        token = secure_session.load_token()
        if token:
            result = _validate_token(token)
            if result is True:
                logger.info("Auth token found and validated — skipping browser auth")
                return
            if result is None:
                # Server error — keep the token, skip browser auth
                logger.info("Token validation inconclusive (server error) — keeping token")
                return
            # Token is definitively invalid (401/403) — clear it
            logger.warning("Clearing stale token from keyring")
            secure_session.delete_token()

        # Environment-variable credentials present (handled at tool-call time)
        if os.getenv("MONARCH_EMAIL") and os.getenv("MONARCH_PASSWORD"):
            logger.info("Environment credentials found — skipping browser auth")
            return

        _auth_guard["active"] = True

    # Spin up the auth server (outside the lock — no need to hold it)
    port = _find_free_port()
    state = _AuthState()

    # Create a handler class that carries our state
    handler_class = type(
        "_BoundAuthHandler",
        (_AuthHandler,),
        {"auth_state": state},
    )

    server = HTTPServer(("127.0.0.1", port), handler_class)
    server.timeout = 1  # unblock handle_request() every second to check state

    def _serve():
        start = time.time()
        logger.info("Auth server listening on http://127.0.0.1:%d", port)
        try:
            while not state.completed:
                server.handle_request()
                if time.time() - start > _AUTH_TIMEOUT:
                    logger.warning(
                        "Auth server timed out after %d seconds — shutting down",
                        _AUTH_TIMEOUT,
                    )
                    break
            server.server_close()
            if state.completed:
                logger.info("Auth server stopped — authentication complete")
        finally:
            with _auth_lock:
                _auth_guard["active"] = False

    thread = threading.Thread(target=_serve, daemon=True, name="monarch-auth-server")
    thread.start()

    url = f"http://127.0.0.1:{port}"
    logger.info("Opening browser for Monarch Money login: %s", url)
    try:
        webbrowser.open(url)
    except Exception:  # pylint: disable=broad-exception-caught
        logger.warning(
            "Could not open browser automatically. "
            "Please visit %s to authenticate.",
            url,
        )
