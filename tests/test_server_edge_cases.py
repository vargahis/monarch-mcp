"""Server edge-case unit tests (12 tests).

Covers get_monarch_client env-credential path, check_auth_status/
debug_session_loading branches, update_transaction goal_id,
refresh_accounts empty, and main().
"""
# pylint: disable=missing-function-docstring

import json
from unittest.mock import patch, AsyncMock

import pytest

from monarch_mcp_server.server import (
    check_auth_status,
    debug_session_loading,
    get_monarch_client,
    main,
    refresh_accounts,
    run_async,
    update_transaction,
)


# ===================================================================
# get_monarch_client — environment credentials
# ===================================================================


def test_get_client_env_credentials(monkeypatch):
    """When keyring has no token, env credentials trigger login + save."""
    monkeypatch.setenv("MONARCH_EMAIL", "user@test.com")
    monkeypatch.setenv("MONARCH_PASSWORD", "secret123")

    mock_client = AsyncMock()
    mock_client.token = "new-tok"

    with (
        patch("monarch_mcp_server.server.secure_session") as mock_ss,
        patch("monarch_mcp_server.server.MonarchMoney", return_value=mock_client),
    ):
        mock_ss.get_authenticated_client.return_value = None

        result = run_async(get_monarch_client())

    assert result is mock_client
    mock_client.login.assert_awaited_once_with("user@test.com", "secret123")
    mock_ss.save_authenticated_session.assert_called_once_with(mock_client)


def test_get_client_env_login_failure(monkeypatch):
    """When env login fails, exception propagates."""
    monkeypatch.setenv("MONARCH_EMAIL", "user@test.com")
    monkeypatch.setenv("MONARCH_PASSWORD", "wrong")

    mock_client = AsyncMock()
    mock_client.login.side_effect = RuntimeError("bad credentials")

    with (
        patch("monarch_mcp_server.server.secure_session") as mock_ss,
        patch("monarch_mcp_server.server.MonarchMoney", return_value=mock_client),
    ):
        mock_ss.get_authenticated_client.return_value = None

        with pytest.raises(RuntimeError, match="bad credentials"):
            run_async(get_monarch_client())


def test_get_client_no_credentials(mock_monarch_client, monkeypatch):
    """When no keyring token and no env vars, trigger_auth_flow + RuntimeError."""
    with patch("monarch_mcp_server.secure_session.keyring") as mock_kr:
        mock_kr.get_password.return_value = None

        monkeypatch.delenv("MONARCH_EMAIL", raising=False)
        monkeypatch.delenv("MONARCH_PASSWORD", raising=False)

        with (
            patch("monarch_mcp_server.server.trigger_auth_flow") as mock_auth,
            pytest.raises(RuntimeError, match="Authentication needed"),
        ):
            run_async(get_monarch_client())

        mock_auth.assert_called_once()


# ===================================================================
# check_auth_status — branches
# ===================================================================


def test_check_auth_no_token():
    with patch("monarch_mcp_server.secure_session.keyring") as mock_kr:
        mock_kr.get_password.return_value = None
        result = check_auth_status()

    assert "No authentication token" in result


def test_check_auth_with_env_email(monkeypatch):
    monkeypatch.setenv("MONARCH_EMAIL", "user@test.com")
    result = check_auth_status()

    assert "user@test.com" in result


def test_check_auth_exception():
    with patch("monarch_mcp_server.server.secure_session") as mock_ss:
        mock_ss.load_token.side_effect = RuntimeError("boom")
        result = check_auth_status()

    assert "Error checking auth status" in result


# ===================================================================
# debug_session_loading — branches
# ===================================================================


def test_debug_session_no_token():
    with patch("monarch_mcp_server.secure_session.keyring") as mock_kr:
        mock_kr.get_password.return_value = None
        result = debug_session_loading()

    assert "No token found" in result


def test_debug_session_exception():
    with patch("monarch_mcp_server.server.secure_session") as mock_ss:
        mock_ss.load_token.side_effect = RuntimeError("keyring busted")
        result = debug_session_loading()

    assert "Keyring access failed" in result


# ===================================================================
# update_transaction — goal_id branch
# ===================================================================


def test_update_transaction_goal_id(mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {"ok": True}
    result = update_transaction(transaction_id="txn-1", goal_id="goal-42")

    data = json.loads(result)
    assert data["ok"] is True
    call_kwargs = mock_monarch_client.update_transaction.call_args[1]
    assert call_kwargs["goal_id"] == "goal-42"


# ===================================================================
# refresh_accounts — empty account list
# ===================================================================


def test_refresh_accounts_empty(mock_monarch_client):
    mock_monarch_client.get_accounts.return_value = {"accounts": []}
    result = refresh_accounts()

    data = json.loads(result)
    assert "error" in data
    assert "No accounts found" in data["error"]


# ===================================================================
# main()
# ===================================================================


def test_main_success():
    with (
        patch("monarch_mcp_server.server.trigger_auth_flow") as mock_auth,
        patch("monarch_mcp_server.server.mcp") as mock_mcp,
    ):
        main()

    mock_auth.assert_called_once()
    mock_mcp.run.assert_called_once()


def test_main_exception():
    with (
        patch("monarch_mcp_server.server.trigger_auth_flow"),
        patch("monarch_mcp_server.server.mcp") as mock_mcp,
    ):
        mock_mcp.run.side_effect = OSError("bind failed")
        with pytest.raises(OSError, match="bind failed"):
            main()
