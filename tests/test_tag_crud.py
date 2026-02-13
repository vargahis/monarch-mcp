"""Phase 5: Tag CRUD tests (13 tests)."""
# pylint: disable=missing-function-docstring

import json

from monarch_mcp_server.server import (
    get_transaction_tags,
    create_transaction_tag,
    delete_transaction_tag,
)

SAMPLE_TAGS_RESPONSE = {
    "householdTransactionTags": [
        {"id": "tag-1", "name": "Vacation", "color": "#19D2A5", "order": 0, "transactionCount": 5},
        {"id": "tag-2", "name": "Tax", "color": "#FF6347", "order": 1, "transactionCount": 12},
    ]
}


# ===================================================================
# 5.1 – list tags
# ===================================================================


def test_list_tags(mock_monarch_client):
    mock_monarch_client.get_transaction_tags.return_value = SAMPLE_TAGS_RESPONSE

    result = json.loads(get_transaction_tags())

    assert len(result) == 2
    assert result[0]["name"] == "Vacation"
    assert result[1]["color"] == "#FF6347"


# ===================================================================
# 5.2 – create tag happy path
# ===================================================================


def test_create_tag_happy(mock_monarch_client):
    mock_monarch_client.create_transaction_tag.return_value = {
        "id": "tag-new",
        "name": "Travel",
        "color": "#19D2A5",
    }

    result = json.loads(create_transaction_tag(name="Travel", color="#19D2A5"))

    assert result["id"] == "tag-new"
    mock_monarch_client.create_transaction_tag.assert_called_once_with(
        "Travel", "#19D2A5"
    )


# ===================================================================
# 5.3 – invalid color "red" -> local validation error
# ===================================================================


def test_create_tag_invalid_color_word(mock_monarch_client):
    result = json.loads(create_transaction_tag(name="Test", color="red"))

    assert "error" in result
    mock_monarch_client.create_transaction_tag.assert_not_called()


# ===================================================================
# 5.4 – short hex "#F00" -> local validation error
# ===================================================================


def test_create_tag_short_hex(mock_monarch_client):
    result = json.loads(create_transaction_tag(name="Test", color="#F00"))

    assert "error" in result
    mock_monarch_client.create_transaction_tag.assert_not_called()


# ===================================================================
# 5.5 – empty name -> local validation error
# ===================================================================


def test_create_tag_empty_name(mock_monarch_client):
    result = json.loads(create_transaction_tag(name="", color="#19D2A5"))

    assert "error" in result
    mock_monarch_client.create_transaction_tag.assert_not_called()


# ===================================================================
# 5.6 – whitespace name -> local validation error
# ===================================================================


def test_create_tag_whitespace_name(mock_monarch_client):
    result = json.loads(create_transaction_tag(name="   ", color="#19D2A5"))

    assert "error" in result
    mock_monarch_client.create_transaction_tag.assert_not_called()


# ===================================================================
# 5.7 – duplicate name -> API accepts (returns new tag)
# ===================================================================


def test_create_tag_duplicate_name(mock_monarch_client):
    mock_monarch_client.create_transaction_tag.return_value = {
        "id": "tag-dup",
        "name": "Vacation",
        "color": "#19D2A5",
    }

    result = json.loads(create_transaction_tag(name="Vacation", color="#19D2A5"))

    assert result["id"] == "tag-dup"


# ===================================================================
# 5.8 – unicode name
# ===================================================================


def test_create_tag_unicode_name(mock_monarch_client):
    mock_monarch_client.create_transaction_tag.return_value = {
        "id": "tag-u",
        "name": "\u65c5\u884c\u2708\ufe0f",
        "color": "#AABBCC",
    }

    result = json.loads(create_transaction_tag(name="\u65c5\u884c\u2708\ufe0f", color="#AABBCC"))

    assert result["name"] == "\u65c5\u884c\u2708\ufe0f"


# ===================================================================
# 5.9 – long name (200+ chars)
# ===================================================================


def test_create_tag_long_name(mock_monarch_client):
    long_name = "A" * 250
    mock_monarch_client.create_transaction_tag.return_value = {
        "id": "tag-long",
        "name": long_name,
        "color": "#112233",
    }

    result = json.loads(create_transaction_tag(name=long_name, color="#112233"))

    assert result["name"] == long_name


# ===================================================================
# 5.10 – special characters
# ===================================================================


def test_create_tag_special_chars(mock_monarch_client):
    special = "Tag & <name> / \"test\""
    mock_monarch_client.create_transaction_tag.return_value = {
        "id": "tag-sp",
        "name": special,
        "color": "#ABCDEF",
    }

    result = json.loads(create_transaction_tag(name=special, color="#ABCDEF"))

    assert result["name"] == special


# ===================================================================
# 5.11 – delete tag happy path
# ===================================================================


def test_delete_tag_happy(mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {
        "deleteTransactionTag": {"__typename": "DeleteTransactionTagPayload"}
    }

    result = json.loads(delete_transaction_tag(tag_id="tag-123"))

    assert result["deleted"] is True
    assert result["tag_id"] == "tag-123"

    call_kwargs = mock_monarch_client.gql_call.call_args[1]
    assert call_kwargs["operation"] == "Common_DeleteTransactionTag"
    assert call_kwargs["variables"] == {"tagId": "tag-123"}


# ===================================================================
# 5.12 – delete tag invalid ID -> API error
# ===================================================================


def test_delete_tag_invalid_id(mock_monarch_client):
    mock_monarch_client.gql_call.side_effect = Exception("Tag not found")

    result = delete_transaction_tag(tag_id="bad-id")

    assert "Error" in result
    assert "Tag not found" in result


# ===================================================================
# 5.13 – delete already-deleted ID -> API error
# ===================================================================


def test_delete_tag_already_deleted(mock_monarch_client):
    mock_monarch_client.gql_call.side_effect = Exception("Tag does not exist")

    result = delete_transaction_tag(tag_id="tag-gone")

    assert "Error" in result
