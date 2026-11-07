"""Phase 1: Authentication tool tests (3 tests)."""
# pylint: disable=missing-function-docstring


async def test_check_auth_status_with_token(mcp_client):
    result = (await mcp_client.call_tool("check_auth_status")).content[0].text
    assert "Authentication token found" in result


async def test_debug_session_loading_with_token(mcp_client):
    result = (await mcp_client.call_tool("debug_session_loading")).content[0].text
    assert "Token found in keyring" in result
    # The token length must not be exposed (near-zero entropy, but no reason to leak).
    assert "length:" not in result


async def test_setup_authentication(mcp_client):
    result = (await mcp_client.call_tool("setup_authentication")).content[0].text
    assert "Authentication" in result
    assert "\n" in result  # multi-line instructions
    assert "get_accounts" in result


async def test_check_auth_status_with_cookies(mcp_client, mock_monarch_client):  # pylint: disable=unused-argument
    from unittest.mock import patch  # pylint: disable=import-outside-toplevel
    with patch("monarch_mcp.secure_session.keyring") as mock_kr:
        mock_kr.get_password.return_value = '{"session_id": "s", "csrftoken": "c"}'
        result = (await mcp_client.call_tool("check_auth_status")).content[0].text
    assert "Authentication cookies found" in result
