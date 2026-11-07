#!/usr/bin/env python3
"""Seed the keyring with Monarch cookie-based auth (no interactive prompts).

Monarch now requires cookie/CSRF auth for many accounts (see
monarchmoneycommunity #41). This logs in using a browser Cookie header string
and stores the validated cookies in the system keyring, where the MCP server's
``secure_session.get_authenticated_client()`` picks them up.

Provide the cookie string via the ``MONARCH_COOKIE`` env var. Environment
variables may be visible to local processes or container administrators.
Get it from your browser:
  DevTools -> Network -> any api.monarch.com/graphql request -> Request Headers
  -> copy the full ``Cookie:`` value (must include session_id and csrftoken).

Usage (Bash; the cookie is read without echoing or entering shell history):
    read -rs MONARCH_COOKIE
    export MONARCH_COOKIE
    python cookie_login.py
    unset MONARCH_COOKIE
"""
import asyncio
import os
import sys

from dotenv import load_dotenv
from monarchmoney import LoginFailedException, MonarchMoney

from monarch_mcp.secure_session import secure_session


async def main() -> int:
    load_dotenv()
    cookie_string = os.environ.get("MONARCH_COOKIE", "").strip()
    if not cookie_string:
        print(
            "ERROR: set MONARCH_COOKIE to your browser's Cookie header value "
            "(must contain session_id and csrftoken).",
            file=sys.stderr,
        )
        return 2

    mm = MonarchMoney()
    try:
        # verify=True does a get_accounts() round-trip to confirm the cookies work.
        # save_session=False: we persist via the keyring, not the lib's pickle file.
        await mm.login_with_cookies(cookie_string, save_session=False, verify=True)
    except LoginFailedException as e:
        print(f"ERROR: cookie login failed: {e}", file=sys.stderr)
        print(
            "Re-copy a fresh Cookie header (cookies expire quickly); ensure "
            "session_id and csrftoken are both present.",
            file=sys.stderr,
        )
        return 1
    except Exception as e:  # noqa: BLE001 - surface the real failure
        print(f"ERROR: unexpected failure: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    secure_session.save_authenticated_session(mm)
    n = len(getattr(mm, "_cookies", {}) or {})
    print(
        f"OK: cookie auth verified and saved to keyring ({n} cookies). "
        "The MCP server will now authenticate via cookies."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
