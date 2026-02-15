"""Phase 1: Authentication tool tests (3 tests)."""
# pylint: disable=missing-function-docstring


async def test_check_auth_status_with_token(mcp_client):
    result = (await mcp_client.call_tool("check_auth_status")).content[0].text
    assert "Authentication token found" in result


async def test_debug_session_loading_with_token(mcp_client):
    result = (await mcp_client.call_tool("debug_session_loading")).content[0].text
    assert "Token found in keyring" in result
    assert "length:" in result


async def test_setup_authentication(mcp_client):
    result = (await mcp_client.call_tool("setup_authentication")).content[0].text
    assert "Authentication" in result
    assert "\n" in result  # multi-line instructions
    assert "get_accounts" in result
