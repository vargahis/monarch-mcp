"""Phase 7: Transaction tagging tests (5 tests)."""
# pylint: disable=missing-function-docstring

import json


async def test_apply_single_tag(mcp_write_client, mock_monarch_client):
    mock_monarch_client.set_transaction_tags.return_value = {
        "setTransactionTags": {"transaction": {"tags": [{"id": "tag-1", "name": "Vacation"}]}}
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "set_transaction_tags", {"transaction_id": "txn-1", "tag_ids": ["tag-1"]}
        )).content[0].text
    )

    assert "setTransactionTags" in result
    mock_monarch_client.set_transaction_tags.assert_called_once_with("txn-1", ["tag-1"])


async def test_apply_multiple_tags(mcp_write_client, mock_monarch_client):
    mock_monarch_client.set_transaction_tags.return_value = {
        "setTransactionTags": {
            "transaction": {
                "tags": [
                    {"id": "tag-1", "name": "Vacation"},
                    {"id": "tag-2", "name": "Tax"},
                ]
            }
        }
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "set_transaction_tags",
            {"transaction_id": "txn-1", "tag_ids": ["tag-1", "tag-2"]},
        )).content[0].text
    )

    tags = result["setTransactionTags"]["transaction"]["tags"]
    assert len(tags) == 2
    mock_monarch_client.set_transaction_tags.assert_called_once_with(
        "txn-1", ["tag-1", "tag-2"]
    )


async def test_remove_all_tags(mcp_write_client, mock_monarch_client):
    mock_monarch_client.set_transaction_tags.return_value = {
        "setTransactionTags": {"transaction": {"tags": []}}
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "set_transaction_tags", {"transaction_id": "txn-1", "tag_ids": []}
        )).content[0].text
    )

    tags = result["setTransactionTags"]["transaction"]["tags"]
    assert tags == []
    mock_monarch_client.set_transaction_tags.assert_called_once_with("txn-1", [])


async def test_invalid_transaction_id(mcp_write_client, mock_monarch_client):
    mock_monarch_client.set_transaction_tags.side_effect = Exception(
        "Transaction not found"
    )

    result = (await mcp_write_client.call_tool(
        "set_transaction_tags", {"transaction_id": "bad-id", "tag_ids": ["tag-1"]}
    )).content[0].text

    assert "Error" in result
    assert "Transaction not found" in result


async def test_nonexistent_tag_id(mcp_write_client, mock_monarch_client):
    mock_monarch_client.set_transaction_tags.side_effect = Exception(
        "Tag not found"
    )

    result = (await mcp_write_client.call_tool(
        "set_transaction_tags", {"transaction_id": "txn-1", "tag_ids": ["bad-tag"]}
    )).content[0].text

    assert "Error" in result
    assert "Tag not found" in result
