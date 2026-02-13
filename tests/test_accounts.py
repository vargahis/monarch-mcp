"""Phase 2: Account tool tests (5 tests)."""
# pylint: disable=missing-function-docstring

import json

from monarch_mcp_server.server import (
    get_accounts,
    get_account_holdings,
    refresh_accounts,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_ACCOUNT = {
    "id": "acc-1",
    "displayName": "Checking",
    "type": {"name": "checking"},
    "currentBalance": 1500.00,
    "institution": {"name": "Chase"},
    "isActive": True,
}

SAMPLE_HOLDING = {
    "id": "hold-1",
    "ticker": "VTI",
    "name": "Vanguard Total Stock Market ETF",
    "quantity": 10.0,
    "value": 2500.00,
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_get_accounts_happy_path(mock_monarch_client):
    mock_monarch_client.get_accounts.return_value = {"accounts": [SAMPLE_ACCOUNT]}

    result = json.loads(get_accounts())

    assert len(result) == 1
    acct = result[0]
    assert acct["id"] == "acc-1"
    assert acct["name"] == "Checking"
    assert acct["type"] == "checking"
    assert acct["balance"] == 1500.00
    assert acct["institution"] == "Chase"
    assert acct["is_active"] is True


def test_get_account_holdings_investment(mock_monarch_client):
    mock_monarch_client.get_account_holdings.return_value = {
        "holdings": [SAMPLE_HOLDING]
    }

    result = json.loads(get_account_holdings(account_id="acc-inv"))

    assert result["holdings"][0]["ticker"] == "VTI"
    mock_monarch_client.get_account_holdings.assert_called_once_with("acc-inv")


def test_get_account_holdings_non_investment(mock_monarch_client):
    mock_monarch_client.get_account_holdings.return_value = {"holdings": []}

    result = json.loads(get_account_holdings(account_id="acc-checking"))

    assert result["holdings"] == []


def test_get_account_holdings_invalid_id(mock_monarch_client):
    mock_monarch_client.get_account_holdings.side_effect = Exception(
        "Account not found"
    )

    result = get_account_holdings(account_id="bad-id")

    assert "Error" in result
    assert "Account not found" in result


def test_refresh_accounts(mock_monarch_client):
    mock_monarch_client.get_accounts.return_value = {
        "accounts": [{"id": "acc-1"}, {"id": "acc-2"}]
    }
    mock_monarch_client.request_accounts_refresh.return_value = {"success": True}

    result = json.loads(refresh_accounts())

    assert result["success"] is True
    mock_monarch_client.get_accounts.assert_called_once()
    mock_monarch_client.request_accounts_refresh.assert_called_once_with(
        ["acc-1", "acc-2"]
    )
