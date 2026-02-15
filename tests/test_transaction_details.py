"""Tests for get_transaction_details tool."""
# pylint: disable=missing-function-docstring

import json


SAMPLE_DETAILS = {
    "getTransaction": {
        "id": "txn-1",
        "date": "2025-01-15",
        "amount": -42.50,
        "merchant": {"name": "Coffee Shop"},
        "category": {"name": "Food & Drink"},
        "notes": "Morning coffee",
        "attachments": [],
        "splitTransactions": [],
        "needsReview": False,
    }
}


async def test_details_happy(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transaction_details.return_value = SAMPLE_DETAILS

    result = json.loads(
        (await mcp_client.call_tool(
            "get_transaction_details", {"transaction_id": "txn-1"}
        )).content[0].text
    )

    assert result["getTransaction"]["id"] == "txn-1"
    mock_monarch_client.get_transaction_details.assert_called_once_with(
        "txn-1", redirect_posted=True,
    )


async def test_details_no_redirect(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transaction_details.return_value = SAMPLE_DETAILS

    await mcp_client.call_tool(
        "get_transaction_details",
        {"transaction_id": "txn-1", "redirect_posted": False},
    )

    mock_monarch_client.get_transaction_details.assert_called_once_with(
        "txn-1", redirect_posted=False,
    )


async def test_details_not_found(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transaction_details.side_effect = Exception(
        "Transaction not found"
    )

    result = (await mcp_client.call_tool(
        "get_transaction_details", {"transaction_id": "bad-id"}
    )).content[0].text

    assert "Error" in result
    assert "Transaction not found" in result


async def test_details_full_data(mcp_client, mock_monarch_client):
    full = {
        "getTransaction": {
            "id": "txn-1",
            "date": "2025-01-15",
            "amount": -100.0,
            "merchant": {"name": "Store"},
            "category": {"name": "Shopping"},
            "notes": "Big purchase",
            "attachments": [{"id": "att-1", "filename": "receipt.pdf"}],
            "splitTransactions": [
                {"id": "split-1", "amount": -60.0},
                {"id": "split-2", "amount": -40.0},
            ],
            "needsReview": True,
        }
    }
    mock_monarch_client.get_transaction_details.return_value = full

    result = json.loads(
        (await mcp_client.call_tool(
            "get_transaction_details", {"transaction_id": "txn-1"}
        )).content[0].text
    )

    txn = result["getTransaction"]
    assert len(txn["attachments"]) == 1
    assert len(txn["splitTransactions"]) == 2
    assert txn["needsReview"] is True
