"""Phase 7: Transaction tagging tests (5 tests)."""

import json

from monarch_mcp_server.server import set_transaction_tags


def test_apply_single_tag(mock_monarch_client):
    mock_monarch_client.set_transaction_tags.return_value = {
        "setTransactionTags": {"transaction": {"tags": [{"id": "tag-1", "name": "Vacation"}]}}
    }

    result = json.loads(set_transaction_tags(transaction_id="txn-1", tag_ids=["tag-1"]))

    assert "setTransactionTags" in result
    mock_monarch_client.set_transaction_tags.assert_called_once_with("txn-1", ["tag-1"])


def test_apply_multiple_tags(mock_monarch_client):
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
        set_transaction_tags(transaction_id="txn-1", tag_ids=["tag-1", "tag-2"])
    )

    tags = result["setTransactionTags"]["transaction"]["tags"]
    assert len(tags) == 2
    mock_monarch_client.set_transaction_tags.assert_called_once_with(
        "txn-1", ["tag-1", "tag-2"]
    )


def test_remove_all_tags(mock_monarch_client):
    mock_monarch_client.set_transaction_tags.return_value = {
        "setTransactionTags": {"transaction": {"tags": []}}
    }

    result = json.loads(set_transaction_tags(transaction_id="txn-1", tag_ids=[]))

    tags = result["setTransactionTags"]["transaction"]["tags"]
    assert tags == []
    mock_monarch_client.set_transaction_tags.assert_called_once_with("txn-1", [])


def test_invalid_transaction_id(mock_monarch_client):
    mock_monarch_client.set_transaction_tags.side_effect = Exception(
        "Transaction not found"
    )

    result = set_transaction_tags(transaction_id="bad-id", tag_ids=["tag-1"])

    assert "Error" in result
    assert "Transaction not found" in result


def test_nonexistent_tag_id(mock_monarch_client):
    mock_monarch_client.set_transaction_tags.side_effect = Exception(
        "Tag not found"
    )

    result = set_transaction_tags(transaction_id="txn-1", tag_ids=["bad-tag"])

    assert "Error" in result
    assert "Tag not found" in result
