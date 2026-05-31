"""Tests for find_merchant_id_by_name and update_recurring_merchant."""
# pylint: disable=missing-function-docstring

import json

import pytest
from fastmcp.exceptions import ToolError


SAMPLE_TRANSACTIONS = {
    "allTransactions": {
        "results": [
            {
                "id": "txn-1",
                "amount": -15.99,
                "date": "2026-04-15",
                "merchant": {"id": "m-netflix", "name": "Netflix"},
                "account": {"displayName": "Visa Card"},
            },
            {
                "id": "txn-2",
                "amount": -15.99,
                "date": "2026-03-15",
                "merchant": {"id": "m-netflix", "name": "Netflix"},
                "account": {"displayName": "Visa Card"},
            },
            {
                "id": "txn-3",
                "amount": -29.00,
                "date": "2026-02-10",
                "merchant": {"id": "m-other", "name": "Netflix DVD"},
                "account": {"displayName": "Visa Card"},
            },
        ]
    }
}


async def test_find_merchant_id_returns_distinct(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = SAMPLE_TRANSACTIONS

    result = json.loads(
        (await mcp_client.call_tool(
            "find_merchant_id_by_name",
            {"name": "Netflix"},
        )).content[0].text
    )

    ids = [r["merchant_id"] for r in result]
    assert ids == ["m-netflix", "m-other"]
    mock_monarch_client.get_transactions.assert_called_once_with(
        search="Netflix", limit=200,
    )


async def test_find_merchant_id_respects_limit(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = SAMPLE_TRANSACTIONS

    result = json.loads(
        (await mcp_client.call_tool(
            "find_merchant_id_by_name",
            {"name": "Netflix", "limit": 1},
        )).content[0].text
    )

    assert len(result) == 1
    assert result[0]["merchant_id"] == "m-netflix"


async def test_find_merchant_id_skips_blank(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = {
        "allTransactions": {
            "results": [
                {"id": "x", "merchant": {}, "amount": 0, "date": "2026-04-01"},
                {"id": "y", "merchant": {"id": "m-z", "name": "Z"},
                 "amount": -1, "date": "2026-04-02"},
            ]
        }
    }

    result = json.loads(
        (await mcp_client.call_tool(
            "find_merchant_id_by_name", {"name": "anything"},
        )).content[0].text
    )

    assert len(result) == 1
    assert result[0]["merchant_id"] == "m-z"


async def test_update_recurring_merchant_passes_args(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_reoccuring.return_value = {
        "updateMerchant": {
            "merchant": {"id": "m-1", "name": "Netflix"},
            "errors": None,
        }
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "update_recurring_merchant",
            {
                "merchant_id": "m-1",
                "name": "Netflix",
                "is_recurring": True,
                "frequency": "monthly",
                "base_date": "2026-01-15",
                "amount": -15.99,
                "is_active": True,
            },
        )).content[0].text
    )

    assert result["updateMerchant"]["merchant"]["id"] == "m-1"
    mock_monarch_client.update_reoccuring.assert_called_once_with(
        merchant_id="m-1",
        name="Netflix",
        is_recurring=True,
        frequency="monthly",
        base_date="2026-01-15",
        amount=-15.99,
        is_active=True,
    )


async def test_update_recurring_merchant_deactivate(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_reoccuring.return_value = {
        "updateMerchant": {"merchant": {"id": "m-2", "name": "OldSub"}, "errors": None}
    }

    # Switching a bill off is a partial edit, but ``is_recurring`` must still be
    # stated — Monarch rejects a recurrence change that omits it. The unchanged
    # schedule fields stay None and Monarch keeps the existing stream values.
    await mcp_write_client.call_tool(
        "update_recurring_merchant",
        {
            "merchant_id": "m-2",
            "name": "OldSub",
            "is_recurring": True,
            "is_active": False,
        },
    )

    mock_monarch_client.update_reoccuring.assert_called_once_with(
        merchant_id="m-2",
        name="OldSub",
        is_recurring=True,
        frequency=None,
        base_date=None,
        amount=None,
        is_active=False,
    )


async def test_update_recurring_merchant_requires_is_recurring(mcp_write_client, mock_monarch_client):
    # ``is_recurring`` is mandatory: Monarch rejects any recurrence change that
    # omits it, so the tool surfaces a missing-argument error before any call.
    with pytest.raises(ToolError, match="is_recurring"):
        await mcp_write_client.call_tool(
            "update_recurring_merchant",
            {"merchant_id": "m-2", "name": "OldSub", "is_active": False},
        )

    mock_monarch_client.update_reoccuring.assert_not_called()


async def test_update_recurring_merchant_disabled_in_read_only(mcp_client, mock_monarch_client):  # pylint: disable=unused-argument
    tools = [t.name for t in (await mcp_client.list_tools())]
    assert "update_recurring_merchant" not in tools
