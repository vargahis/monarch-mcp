"""Tests for transaction category tools."""
# pylint: disable=missing-function-docstring

import json
from datetime import datetime


SAMPLE_CATEGORIES = {
    "categories": [
        {
            "id": "cat-1",
            "name": "Groceries",
            "order": 0,
            "isSystemCategory": False,
            "isDisabled": False,
            "group": {"id": "grp-1", "name": "Food & Drink", "type": "expense"},
        },
        {
            "id": "cat-2",
            "name": "Salary",
            "order": 0,
            "isSystemCategory": True,
            "isDisabled": False,
            "group": {"id": "grp-2", "name": "Income", "type": "income"},
        },
    ]
}

SAMPLE_GROUPS = {
    "categoryGroups": [
        {"id": "grp-1", "name": "Food & Drink", "order": 0, "type": "expense"},
        {"id": "grp-2", "name": "Income", "order": 1, "type": "income"},
    ]
}


# ===================================================================
# get_transaction_categories
# ===================================================================


async def test_get_categories_happy(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transaction_categories.return_value = SAMPLE_CATEGORIES

    result = json.loads(
        (await mcp_client.call_tool("get_transaction_categories")).content[0].text
    )

    assert len(result["categories"]) == 2
    assert result["categories"][0]["name"] == "Groceries"
    mock_monarch_client.get_transaction_categories.assert_called_once()


async def test_get_categories_empty(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transaction_categories.return_value = {"categories": []}

    result = json.loads(
        (await mcp_client.call_tool("get_transaction_categories")).content[0].text
    )

    assert result["categories"] == []


async def test_get_categories_error(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transaction_categories.side_effect = Exception("API down")

    result = (await mcp_client.call_tool("get_transaction_categories")).content[0].text

    assert "Error" in result


# ===================================================================
# get_transaction_category_groups
# ===================================================================


async def test_get_category_groups_happy(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transaction_category_groups.return_value = SAMPLE_GROUPS

    result = json.loads(
        (await mcp_client.call_tool("get_transaction_category_groups")).content[0].text
    )

    assert len(result["categoryGroups"]) == 2
    mock_monarch_client.get_transaction_category_groups.assert_called_once()


async def test_get_category_groups_empty(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transaction_category_groups.return_value = {
        "categoryGroups": []
    }

    result = json.loads(
        (await mcp_client.call_tool("get_transaction_category_groups")).content[0].text
    )

    assert result["categoryGroups"] == []


# ===================================================================
# create_transaction_category
# ===================================================================


async def test_create_category_happy(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_transaction_category.return_value = {
        "id": "cat-new",
        "name": "Coffee",
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_category", {"group_id": "grp-1", "name": "Coffee"}
        )).content[0].text
    )

    assert result["name"] == "Coffee"
    call_kwargs = mock_monarch_client.create_transaction_category.call_args[1]
    assert call_kwargs["group_id"] == "grp-1"
    assert call_kwargs["transaction_category_name"] == "Coffee"
    assert call_kwargs["icon"] == "\u2753"
    assert call_kwargs["rollover_enabled"] is False


async def test_create_category_with_rollover(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_transaction_category.return_value = {
        "id": "cat-new",
        "name": "Rent",
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_category",
            {
                "group_id": "grp-1",
                "name": "Rent",
                "rollover_enabled": True,
                "rollover_start_month": "2025-01-01",
            },
        )).content[0].text
    )

    assert result["name"] == "Rent"
    call_kwargs = mock_monarch_client.create_transaction_category.call_args[1]
    assert call_kwargs["rollover_enabled"] is True
    assert call_kwargs["rollover_start_month"] == datetime(2025, 1, 1)


async def test_create_category_custom_icon(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_transaction_category.return_value = {
        "id": "cat-new",
        "name": "Gaming",
    }

    await mcp_write_client.call_tool(
        "create_transaction_category",
        {"group_id": "grp-1", "name": "Gaming", "icon": "\U0001F3AE"},
    )

    call_kwargs = mock_monarch_client.create_transaction_category.call_args[1]
    assert call_kwargs["icon"] == "\U0001F3AE"


async def test_create_category_error(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_transaction_category.side_effect = Exception(
        "Group not found"
    )

    result = (await mcp_write_client.call_tool(
        "create_transaction_category", {"group_id": "bad-grp", "name": "Test"}
    )).content[0].text

    assert "Error" in result


# ===================================================================
# delete_transaction_category
# ===================================================================


async def test_delete_category_happy(mcp_write_client, mock_monarch_client):
    mock_monarch_client.delete_transaction_category.return_value = True

    result = json.loads(
        (await mcp_write_client.call_tool(
            "delete_transaction_category", {"category_id": "cat-1"}
        )).content[0].text
    )

    assert result["deleted"] is True
    assert result["category_id"] == "cat-1"
    assert result["result"] is True
    mock_monarch_client.delete_transaction_category.assert_called_once_with("cat-1")


async def test_delete_category_error(mcp_write_client, mock_monarch_client):
    mock_monarch_client.delete_transaction_category.side_effect = Exception(
        "Category not found"
    )

    result = (await mcp_write_client.call_tool(
        "delete_transaction_category", {"category_id": "bad-cat"}
    )).content[0].text

    assert "Error" in result
