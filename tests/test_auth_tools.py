"""Phase 1: Authentication tool tests (3 tests)."""
# pylint: disable=missing-function-docstring

from monarch_mcp_server.server import (
    check_auth_status,
    debug_session_loading,
    setup_authentication,
)


def test_check_auth_status_with_token():
    result = check_auth_status()
    assert "Authentication token found" in result


def test_debug_session_loading_with_token():
    result = debug_session_loading()
    assert "Token found in keyring" in result
    assert "length:" in result


def test_setup_authentication():
    result = setup_authentication()
    assert "Authentication" in result
    assert "\n" in result  # multi-line instructions
    assert "get_accounts" in result
