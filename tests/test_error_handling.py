"""Exception handling tests for run_async, MCP tool decorator, and auth handlers."""
# pylint: disable=missing-function-docstring,protected-access

from unittest.mock import patch, Mock

import pytest
from gql.transport.exceptions import TransportServerError, TransportQueryError, TransportError
from monarchmoney import LoginFailedException

from monarch_mcp_server.server import run_async
from monarch_mcp_server.auth_server import _AuthHandler, _AuthState


# ===================================================================
# run_async — narrowed exception handling
# ===================================================================


def test_run_async_auth_401_triggers_recovery():
    """TransportServerError 401 triggers token deletion and re-auth."""
    async def _failing():
        raise TransportServerError("Unauthorized", code=401)

    with (
        patch("monarch_mcp_server.server.secure_session") as mock_session,
        patch("monarch_mcp_server.server.trigger_auth_flow") as mock_auth,
    ):
        with pytest.raises(RuntimeError, match="session has expired"):
            run_async(_failing())

        mock_session.delete_token.assert_called_once()
        mock_auth.assert_called_once()


def test_run_async_login_failed_triggers_recovery():
    """LoginFailedException triggers token deletion and re-auth."""
    async def _failing():
        raise LoginFailedException()

    with (
        patch("monarch_mcp_server.server.secure_session") as mock_session,
        patch("monarch_mcp_server.server.trigger_auth_flow") as mock_auth,
    ):
        with pytest.raises(RuntimeError, match="session has expired"):
            run_async(_failing())

        mock_session.delete_token.assert_called_once()
        mock_auth.assert_called_once()


def test_run_async_non_auth_500_propagates():
    """Non-auth TransportServerError (500) propagates without recovery."""
    async def _failing():
        raise TransportServerError("Internal Server Error", code=500)

    with (
        patch("monarch_mcp_server.server.secure_session") as mock_session,
        patch("monarch_mcp_server.server.trigger_auth_flow") as mock_auth,
    ):
        with pytest.raises(TransportServerError):
            run_async(_failing())

        mock_session.delete_token.assert_not_called()
        mock_auth.assert_not_called()


def test_run_async_generic_exception_propagates():
    """Generic exceptions bypass run_async entirely — not caught."""
    async def _failing():
        raise ValueError("something went wrong")

    with (
        patch("monarch_mcp_server.server.secure_session") as mock_session,
        patch("monarch_mcp_server.server.trigger_auth_flow") as mock_auth,
    ):
        with pytest.raises(ValueError, match="something went wrong"):
            run_async(_failing())

        mock_session.delete_token.assert_not_called()
        mock_auth.assert_not_called()


def test_run_async_transport_query_error_propagates():
    """TransportQueryError is not caught by run_async."""
    async def _failing():
        raise TransportQueryError("Invalid query")

    with (
        patch("monarch_mcp_server.server.secure_session") as mock_session,
        patch("monarch_mcp_server.server.trigger_auth_flow") as mock_auth,
    ):
        with pytest.raises(TransportQueryError):
            run_async(_failing())

        mock_session.delete_token.assert_not_called()
        mock_auth.assert_not_called()


# ===================================================================
# MCP tool decorator — exception type discrimination (via Client)
# ===================================================================


async def test_tool_runtime_error(mcp_client, mock_monarch_client):
    """RuntimeError (e.g., auth recovery) returns error string."""
    mock_monarch_client.get_accounts.side_effect = RuntimeError("session expired")

    result = (await mcp_client.call_tool("get_accounts")).content[0].text

    assert "Error" in result
    assert "session expired" in result


async def test_tool_transport_server_error(mcp_client, mock_monarch_client):
    """TransportServerError includes HTTP status code in error."""
    mock_monarch_client.get_accounts.side_effect = TransportServerError(
        "Internal Server Error", code=500,
    )

    result = (await mcp_client.call_tool("get_accounts")).content[0].text

    assert "Error" in result
    assert "500" in result


async def test_tool_transport_query_error(mcp_client, mock_monarch_client):
    """TransportQueryError returns query-specific error."""
    mock_monarch_client.get_accounts.side_effect = TransportQueryError(
        "Validation error",
    )

    result = (await mcp_client.call_tool("get_accounts")).content[0].text

    assert "Error" in result
    assert "query" in result.lower()


async def test_tool_transport_error(mcp_client, mock_monarch_client):
    """TransportError returns connection-specific error."""
    mock_monarch_client.get_accounts.side_effect = TransportError(
        "Connection refused",
    )

    result = (await mcp_client.call_tool("get_accounts")).content[0].text

    assert "Error" in result
    assert "connection" in result.lower()


async def test_tool_unexpected_error(mcp_client, mock_monarch_client):
    """Generic Exception returns catch-all error."""
    mock_monarch_client.get_accounts.side_effect = ValueError("weird error")

    result = (await mcp_client.call_tool("get_accounts")).content[0].text

    assert "Error" in result
    assert "weird error" in result


# ===================================================================
# Auth server handlers — exception type discrimination
# ===================================================================


def _make_handler():
    """Create an _AuthHandler for unit testing without HTTP plumbing."""
    handler = object.__new__(_AuthHandler)
    handler.auth_state = _AuthState()
    handler._send_json = Mock()  # pylint: disable=protected-access
    return handler


# --- _handle_login ---

def test_login_handler_bad_credentials():
    handler = _make_handler()
    with (
        patch("monarch_mcp_server.auth_server.MonarchMoney"),
        patch(
            "monarch_mcp_server.auth_server._run_sync",
            side_effect=LoginFailedException(),
        ),
    ):
        handler._handle_login({"email": "a@b.com", "password": "wrong"})

    response = handler._send_json.call_args[0][0]
    assert "error" in response
    assert "Invalid email or password" in response["error"]


def test_login_handler_transport_server_error():
    handler = _make_handler()
    with (
        patch("monarch_mcp_server.auth_server.MonarchMoney"),
        patch(
            "monarch_mcp_server.auth_server._run_sync",
            side_effect=TransportServerError("Server Error", code=500),
        ),
    ):
        handler._handle_login({"email": "a@b.com", "password": "pass"})

    response = handler._send_json.call_args[0][0]
    assert "error" in response
    assert "500" in response["error"]


def test_login_handler_unexpected_error():
    handler = _make_handler()
    with (
        patch("monarch_mcp_server.auth_server.MonarchMoney"),
        patch(
            "monarch_mcp_server.auth_server._run_sync",
            side_effect=OSError("network down"),
        ),
    ):
        handler._handle_login({"email": "a@b.com", "password": "pass"})

    response = handler._send_json.call_args[0][0]
    assert "error" in response
    assert "network down" in response["error"]


# --- _handle_mfa ---

def _make_mfa_handler():
    """Create a handler in the awaiting-MFA state."""
    handler = _make_handler()
    handler.auth_state.email = "a@b.com"
    handler.auth_state.password = "pass"
    handler.auth_state.awaiting_mfa = True
    return handler


def test_mfa_handler_bad_code():
    handler = _make_mfa_handler()
    with (
        patch("monarch_mcp_server.auth_server.MonarchMoney"),
        patch(
            "monarch_mcp_server.auth_server._run_sync",
            side_effect=LoginFailedException(),
        ),
    ):
        handler._handle_mfa({"code": "000000"})

    response = handler._send_json.call_args[0][0]
    assert "error" in response
    assert "Invalid authentication code" in response["error"]


def test_mfa_handler_transport_server_error():
    handler = _make_mfa_handler()
    with (
        patch("monarch_mcp_server.auth_server.MonarchMoney"),
        patch(
            "monarch_mcp_server.auth_server._run_sync",
            side_effect=TransportServerError("Server Error", code=503),
        ),
    ):
        handler._handle_mfa({"code": "123456"})

    response = handler._send_json.call_args[0][0]
    assert "error" in response
    assert "503" in response["error"]


def test_mfa_handler_unexpected_error():
    handler = _make_mfa_handler()
    with (
        patch("monarch_mcp_server.auth_server.MonarchMoney"),
        patch(
            "monarch_mcp_server.auth_server._run_sync",
            side_effect=OSError("timeout"),
        ),
    ):
        handler._handle_mfa({"code": "123456"})

    response = handler._send_json.call_args[0][0]
    assert "error" in response
    assert "timeout" in response["error"]
