"""Auth handler unit tests (20 tests).

Covers _AuthHandler routing (do_GET, do_POST), login/MFA logic,
_send_json/_send_html helpers, log_message, _find_free_port,
and _validate_token.
"""
# pylint: disable=missing-function-docstring,protected-access

import io
import json
from unittest.mock import patch, Mock, MagicMock

import pytest
from monarchmoney import RequireMFAException

from monarch_mcp.auth_server import (
    _AuthHandler,
    _AuthState,
    _find_free_port,
    _validate_token,
)


# ── Handler factory ───────────────────────────────────────────────


def _make_handler(path="/", method="GET", body=None):
    """Create an _AuthHandler wired for unit testing without sockets."""
    handler = object.__new__(_AuthHandler)
    handler.auth_state = _AuthState()
    handler.path = path

    # Wire up the response plumbing
    handler.wfile = io.BytesIO()
    handler.send_response = Mock()
    handler.send_header = Mock()
    handler.end_headers = Mock()
    handler.send_error = Mock()

    # Wire up request body for POST
    if body is not None:
        raw = json.dumps(body).encode() if isinstance(body, dict) else body
        handler.rfile = io.BytesIO(raw)
        handler.headers = {"Content-Length": str(len(raw))}
    else:
        handler.rfile = io.BytesIO(b"")
        handler.headers = {"Content-Length": "0"}

    return handler


# ===================================================================
# _handle_login — validation
# ===================================================================


def test_login_empty_email():
    handler = _make_handler()
    handler._send_json = Mock()
    handler._handle_login({"email": "", "password": "secret"})

    resp = handler._send_json.call_args[0][0]
    assert "error" in resp
    assert "required" in resp["error"].lower()


def test_login_empty_password():
    handler = _make_handler()
    handler._send_json = Mock()
    handler._handle_login({"email": "a@b.com", "password": ""})

    resp = handler._send_json.call_args[0][0]
    assert "error" in resp


# ===================================================================
# _handle_login — success and MFA
# ===================================================================


def test_login_success_no_mfa():
    handler = _make_handler()
    handler._send_json = Mock()
    with (
        patch("monarch_mcp.auth_server.MonarchMoney"),
        patch("monarch_mcp.auth_server._run_sync"),
        patch("monarch_mcp.auth_server.secure_session") as mock_ss,
    ):
        handler._handle_login({"email": "a@b.com", "password": "pass"})

    mock_ss.save_authenticated_session.assert_called_once()
    assert handler.auth_state.completed is True
    resp = handler._send_json.call_args[0][0]
    assert resp["success"] is True


def test_login_mfa_required():
    handler = _make_handler()
    handler._send_json = Mock()
    with (
        patch("monarch_mcp.auth_server.MonarchMoney"),
        patch(
            "monarch_mcp.auth_server._run_sync",
            side_effect=RequireMFAException(),
        ),
    ):
        handler._handle_login({"email": "a@b.com", "password": "pass"})

    assert handler.auth_state.awaiting_mfa is True
    assert handler.auth_state.email == "a@b.com"
    resp = handler._send_json.call_args[0][0]
    assert resp["mfa_required"] is True


# ===================================================================
# _handle_mfa — validation and success
# ===================================================================


def test_mfa_empty_code():
    handler = _make_handler()
    handler._send_json = Mock()
    handler.auth_state.awaiting_mfa = True
    handler._handle_mfa({"code": ""})

    resp = handler._send_json.call_args[0][0]
    assert "error" in resp
    assert "required" in resp["error"].lower()


def test_mfa_no_pending_challenge():
    handler = _make_handler()
    handler._send_json = Mock()
    handler.auth_state.awaiting_mfa = False
    handler._handle_mfa({"code": "123456"})

    resp = handler._send_json.call_args[0][0]
    assert "error" in resp
    assert "No pending MFA" in resp["error"]


def test_mfa_success():
    handler = _make_handler()
    handler._send_json = Mock()
    handler.auth_state.email = "a@b.com"
    handler.auth_state.password = "pass"
    handler.auth_state.awaiting_mfa = True

    with (
        patch("monarch_mcp.auth_server.MonarchMoney"),
        patch("monarch_mcp.auth_server._run_sync"),
        patch("monarch_mcp.auth_server.secure_session") as mock_ss,
    ):
        handler._handle_mfa({"code": "123456"})

    mock_ss.save_authenticated_session.assert_called_once()
    assert handler.auth_state.completed is True
    resp = handler._send_json.call_args[0][0]
    assert resp["success"] is True


# ===================================================================
# _send_json / _send_html
# ===================================================================


def test_send_json():
    handler = _make_handler()
    handler._send_json({"key": "value"})

    handler.send_response.assert_called_once_with(200)
    # Check Content-Type header
    ct_calls = [
        c for c in handler.send_header.call_args_list
        if c[0][0] == "Content-Type"
    ]
    assert ct_calls[0][0][1] == "application/json"
    written = handler.wfile.getvalue()
    assert json.loads(written) == {"key": "value"}


def test_send_html():
    handler = _make_handler()
    handler._send_html("<h1>Hello</h1>")

    handler.send_response.assert_called_once_with(200)
    ct_calls = [
        c for c in handler.send_header.call_args_list
        if c[0][0] == "Content-Type"
    ]
    assert "text/html" in ct_calls[0][0][1]
    written = handler.wfile.getvalue()
    assert b"<h1>Hello</h1>" in written


# ===================================================================
# log_message
# ===================================================================


def test_log_message():
    handler = _make_handler()
    with patch("monarch_mcp.auth_server.logger") as mock_log:
        handler.log_message("request %s %s", "GET", "/")

    mock_log.debug.assert_called_once()
    assert "GET" in mock_log.debug.call_args[0][1]


# ===================================================================
# do_GET routing
# ===================================================================


def test_do_get_root():
    handler = _make_handler(path="/")
    handler._send_html = Mock()
    handler.do_GET()

    handler._send_html.assert_called_once()
    assert "Monarch" in handler._send_html.call_args[0][0]


def test_do_get_404():
    handler = _make_handler(path="/nonexistent")
    handler.do_GET()

    handler.send_error.assert_called_once_with(404)


# ===================================================================
# do_POST routing
# ===================================================================


def test_do_post_login_route():
    handler = _make_handler(path="/login", body={"email": "", "password": ""})
    handler._send_json = Mock()
    handler.do_POST()

    # Should reach _handle_login which validates empty fields
    handler._send_json.assert_called_once()
    resp = handler._send_json.call_args[0][0]
    assert "error" in resp


def test_do_post_mfa_route():
    handler = _make_handler(path="/mfa", body={"code": ""})
    handler._send_json = Mock()
    handler.do_POST()

    handler._send_json.assert_called_once()
    resp = handler._send_json.call_args[0][0]
    assert "error" in resp


def test_do_post_unknown_route():
    handler = _make_handler(path="/unknown", body={})
    handler.do_POST()

    handler.send_error.assert_called_once_with(404)


def test_do_post_invalid_json():
    handler = _make_handler(path="/login")
    handler.rfile = io.BytesIO(b"not-json{{{")
    handler.headers = {"Content-Length": "11"}
    handler._send_json = Mock()

    handler.do_POST()

    resp = handler._send_json.call_args[0][0]
    assert "Invalid request body" in resp["error"]


# ===================================================================
# _find_free_port
# ===================================================================


def test_find_free_port():
    port = _find_free_port()
    assert isinstance(port, int)
    assert port > 0


# ===================================================================
# _validate_token
# ===================================================================


def test_validate_token_valid():
    with (
        patch("monarch_mcp.auth_server.MonarchMoney") as mock_cls,
        patch("monarch_mcp.auth_server._run_sync"),
    ):
        mock_cls.return_value = MagicMock()
        result = _validate_token("good-token")

    assert result is True


def test_validate_token_auth_error():
    from gql.transport.exceptions import TransportServerError  # pylint: disable=import-outside-toplevel

    with (
        patch("monarch_mcp.auth_server.MonarchMoney"),
        patch(
            "monarch_mcp.auth_server._run_sync",
            side_effect=TransportServerError("Unauthorized", code=401),
        ),
    ):
        result = _validate_token("bad-token")

    assert result is False


def test_validate_token_server_error():
    with (
        patch("monarch_mcp.auth_server.MonarchMoney"),
        patch(
            "monarch_mcp.auth_server._run_sync",
            side_effect=OSError("network down"),
        ),
    ):
        result = _validate_token("some-token")

    assert result is None
