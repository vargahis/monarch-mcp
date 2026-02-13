"""Core fixtures for Monarch Money MCP Server tests.

Mocking strategy — only 3rd-party code is mocked:
  1. keyring           -> patched in secure_session to return fake tokens
  2. MonarchMoney class -> patched in secure_session so constructor returns AsyncMock
  3. trigger_auth_flow  -> patched in server to prevent browser opening
"""

from unittest.mock import patch, AsyncMock  # pylint: disable=unused-import

import pytest


@pytest.fixture
def mock_monarch_client():
    """Patches keyring + MonarchMoney constructor.  Yields AsyncMock client."""
    with (
        patch("monarch_mcp_server.secure_session.keyring") as mock_kr,
        patch("monarch_mcp_server.secure_session.MonarchMoney") as mock_cls,
    ):
        mock_kr.get_password.return_value = "fake-token"
        client = AsyncMock()
        client.token = "fake-token"
        mock_cls.return_value = client
        yield client


@pytest.fixture(autouse=True)
def _isolate(mock_monarch_client, monkeypatch):  # pylint: disable=redefined-outer-name,unused-argument
    """Autouse: every test gets mock client, no browser auth, no env leaks."""
    monkeypatch.delenv("MONARCH_EMAIL", raising=False)
    monkeypatch.delenv("MONARCH_PASSWORD", raising=False)
    with patch("monarch_mcp_server.server.trigger_auth_flow"):
        yield
