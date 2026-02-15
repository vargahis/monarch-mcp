"""Phase 5: Tag CRUD tests (13 tests)."""
# pylint: disable=missing-function-docstring

import json


SAMPLE_TAGS_RESPONSE = {
    "householdTransactionTags": [
        {"id": "tag-1", "name": "Vacation", "color": "#19D2A5", "order": 0, "transactionCount": 5},
        {"id": "tag-2", "name": "Tax", "color": "#FF6347", "order": 1, "transactionCount": 12},
    ]
}


# ===================================================================
# 5.1 – list tags
# ===================================================================


async def test_list_tags(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transaction_tags.return_value = SAMPLE_TAGS_RESPONSE

    result = json.loads(
        (await mcp_client.call_tool("get_transaction_tags")).content[0].text
    )

    assert len(result) == 2
    assert result[0]["name"] == "Vacation"
    assert result[1]["color"] == "#FF6347"


# ===================================================================
# 5.2 – create tag happy path
# ===================================================================


async def test_create_tag_happy(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_transaction_tag.return_value = {
        "id": "tag-new",
        "name": "Travel",
        "color": "#19D2A5",
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_tag", {"name": "Travel", "color": "#19D2A5"}
        )).content[0].text
    )

    assert result["id"] == "tag-new"
    mock_monarch_client.create_transaction_tag.assert_called_once_with(
        "Travel", "#19D2A5"
    )


# ===================================================================
# 5.3 – invalid color "red" -> local validation error
# ===================================================================


async def test_create_tag_invalid_color_word(mcp_write_client, mock_monarch_client):
    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_tag", {"name": "Test", "color": "red"}
        )).content[0].text
    )

    assert "error" in result
    mock_monarch_client.create_transaction_tag.assert_not_called()


# ===================================================================
# 5.4 – short hex "#F00" -> local validation error
# ===================================================================


async def test_create_tag_short_hex(mcp_write_client, mock_monarch_client):
    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_tag", {"name": "Test", "color": "#F00"}
        )).content[0].text
    )

    assert "error" in result
    mock_monarch_client.create_transaction_tag.assert_not_called()


# ===================================================================
# 5.5 – empty name -> local validation error
# ===================================================================


async def test_create_tag_empty_name(mcp_write_client, mock_monarch_client):
    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_tag", {"name": "", "color": "#19D2A5"}
        )).content[0].text
    )

    assert "error" in result
    mock_monarch_client.create_transaction_tag.assert_not_called()


# ===================================================================
# 5.6 – whitespace name -> local validation error
# ===================================================================


async def test_create_tag_whitespace_name(mcp_write_client, mock_monarch_client):
    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_tag", {"name": "   ", "color": "#19D2A5"}
        )).content[0].text
    )

    assert "error" in result
    mock_monarch_client.create_transaction_tag.assert_not_called()


# ===================================================================
# 5.7 – duplicate name -> API accepts (returns new tag)
# ===================================================================


async def test_create_tag_duplicate_name(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_transaction_tag.return_value = {
        "id": "tag-dup",
        "name": "Vacation",
        "color": "#19D2A5",
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_tag", {"name": "Vacation", "color": "#19D2A5"}
        )).content[0].text
    )

    assert result["id"] == "tag-dup"


# ===================================================================
# 5.8 – unicode name
# ===================================================================


async def test_create_tag_unicode_name(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_transaction_tag.return_value = {
        "id": "tag-u",
        "name": "\u65c5\u884c\u2708\ufe0f",
        "color": "#AABBCC",
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_tag",
            {"name": "\u65c5\u884c\u2708\ufe0f", "color": "#AABBCC"},
        )).content[0].text
    )

    assert result["name"] == "\u65c5\u884c\u2708\ufe0f"


# ===================================================================
# 5.9 – long name (200+ chars)
# ===================================================================


async def test_create_tag_long_name(mcp_write_client, mock_monarch_client):
    long_name = "A" * 250
    mock_monarch_client.create_transaction_tag.return_value = {
        "id": "tag-long",
        "name": long_name,
        "color": "#112233",
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_tag", {"name": long_name, "color": "#112233"}
        )).content[0].text
    )

    assert result["name"] == long_name


# ===================================================================
# 5.10 – special characters
# ===================================================================


async def test_create_tag_special_chars(mcp_write_client, mock_monarch_client):
    special = "Tag & <name> / \"test\""
    mock_monarch_client.create_transaction_tag.return_value = {
        "id": "tag-sp",
        "name": special,
        "color": "#ABCDEF",
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_tag", {"name": special, "color": "#ABCDEF"}
        )).content[0].text
    )

    assert result["name"] == special


# ===================================================================
# 5.11 – delete tag happy path
# ===================================================================


async def test_delete_tag_happy(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {
        "deleteTransactionTag": {"__typename": "DeleteTransactionTagPayload"}
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "delete_transaction_tag", {"tag_id": "tag-123"}
        )).content[0].text
    )

    assert result["deleted"] is True
    assert result["tag_id"] == "tag-123"

    call_kwargs = mock_monarch_client.gql_call.call_args[1]
    assert call_kwargs["operation"] == "Common_DeleteTransactionTag"
    assert call_kwargs["variables"] == {"tagId": "tag-123"}


# ===================================================================
# 5.12 – delete tag invalid ID -> API error
# ===================================================================


async def test_delete_tag_invalid_id(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.side_effect = Exception("Tag not found")

    result = (await mcp_write_client.call_tool(
        "delete_transaction_tag", {"tag_id": "bad-id"}
    )).content[0].text

    assert "Error" in result
    assert "Tag not found" in result


# ===================================================================
# 5.13 – delete already-deleted ID -> API error
# ===================================================================


async def test_delete_tag_already_deleted(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.side_effect = Exception("Tag does not exist")

    result = (await mcp_write_client.call_tool(
        "delete_transaction_tag", {"tag_id": "tag-gone"}
    )).content[0].text

    assert "Error" in result
