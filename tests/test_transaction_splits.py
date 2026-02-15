"""Tests for transaction split tools."""
# pylint: disable=missing-function-docstring

import json


SAMPLE_SPLITS = {
    "getTransaction": {
        "id": "txn-1",
        "splitTransactions": [
            {"id": "split-1", "amount": -60.0, "merchant": {"name": "Store A"}},
            {"id": "split-2", "amount": -40.0, "merchant": {"name": "Store B"}},
        ],
    }
}


# ===================================================================
# get_transaction_splits
# ===================================================================


async def test_get_splits_happy(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transaction_splits.return_value = SAMPLE_SPLITS

    result = json.loads(
        (await mcp_client.call_tool(
            "get_transaction_splits", {"transaction_id": "txn-1"}
        )).content[0].text
    )

    splits = result["getTransaction"]["splitTransactions"]
    assert len(splits) == 2
    mock_monarch_client.get_transaction_splits.assert_called_once_with("txn-1")


async def test_get_splits_empty(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transaction_splits.return_value = {
        "getTransaction": {"id": "txn-1", "splitTransactions": []}
    }

    result = json.loads(
        (await mcp_client.call_tool(
            "get_transaction_splits", {"transaction_id": "txn-1"}
        )).content[0].text
    )

    assert result["getTransaction"]["splitTransactions"] == []


async def test_get_splits_error(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transaction_splits.side_effect = Exception(
        "Transaction not found"
    )

    result = (await mcp_client.call_tool(
        "get_transaction_splits", {"transaction_id": "bad-id"}
    )).content[0].text

    assert "Error" in result


# ===================================================================
# update_transaction_splits
# ===================================================================


async def test_update_splits_happy(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_transaction_splits.return_value = {
        "updateTransactionSplits": {"id": "txn-1"}
    }

    split_data = [
        {"merchantName": "Store A", "amount": -60.0, "categoryId": "cat-1"},
        {"merchantName": "Store B", "amount": -40.0, "categoryId": "cat-2"},
    ]
    result = json.loads(
        (await mcp_write_client.call_tool(
            "update_transaction_splits",
            {"transaction_id": "txn-1", "split_data": split_data},
        )).content[0].text
    )

    assert "updateTransactionSplits" in result
    mock_monarch_client.update_transaction_splits.assert_called_once_with(
        "txn-1", split_data
    )


async def test_update_splits_remove_all(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_transaction_splits.return_value = {
        "updateTransactionSplits": {"id": "txn-1"}
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "update_transaction_splits",
            {"transaction_id": "txn-1", "split_data": []},
        )).content[0].text
    )

    assert "updateTransactionSplits" in result
    mock_monarch_client.update_transaction_splits.assert_called_once_with("txn-1", [])


async def test_update_splits_error(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_transaction_splits.side_effect = Exception(
        "Split amounts don't match"
    )

    result = (await mcp_write_client.call_tool(
        "update_transaction_splits",
        {
            "transaction_id": "txn-1",
            "split_data": [{"merchantName": "X", "amount": -50.0, "categoryId": "cat-1"}],
        },
    )).content[0].text

    assert "Error" in result
