"""Bonus: is_auth_error + run_async auth recovery tests (6 tests)."""

import pytest
from unittest.mock import patch

from gql.transport.exceptions import TransportServerError
from monarchmoney import LoginFailedException

from monarch_mcp_server.secure_session import is_auth_error
from monarch_mcp_server.server import run_async


# ===================================================================
# is_auth_error unit tests
# ===================================================================


def test_transport_401():
    exc = TransportServerError("Unauthorized", code=401)
    assert is_auth_error(exc) is True


def test_transport_403_json():
    cause = Exception("403 Forbidden")
    cause.headers = {"content-type": "application/json"}
    exc = TransportServerError("Forbidden", code=403)
    exc.__cause__ = cause
    assert is_auth_error(exc) is True


def test_transport_403_html_waf():
    cause = Exception("403 Forbidden")
    cause.headers = {"content-type": "text/html"}
    exc = TransportServerError("Forbidden", code=403)
    exc.__cause__ = cause
    assert is_auth_error(exc) is False


def test_login_failed():
    exc = LoginFailedException()
    assert is_auth_error(exc) is True


def test_generic_exception():
    assert is_auth_error(Exception("random error")) is False


# ===================================================================
# run_async auth-error recovery
# ===================================================================


def test_run_async_auth_error_recovery():
    """Auth error in run_async → token deleted, re-auth triggered, RuntimeError raised."""
    exc = TransportServerError("Unauthorized", code=401)

    async def _failing():
        raise exc

    with (
        patch("monarch_mcp_server.server.secure_session") as mock_session,
        patch("monarch_mcp_server.server.trigger_auth_flow") as mock_auth,
    ):
        with pytest.raises(RuntimeError, match="session has expired"):
            run_async(_failing())

        mock_session.delete_token.assert_called_once()
        mock_auth.assert_called_once()
