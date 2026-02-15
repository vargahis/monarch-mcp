"""Tests for get_recurring_transactions tool."""
# pylint: disable=missing-function-docstring

import json


SAMPLE_RECURRING = {
    "recurringTransactions": [
        {
            "id": "rec-1",
            "amount": -15.99,
            "merchant": {"name": "Netflix"},
            "frequency": "monthly",
            "account": {"displayName": "Checking"},
            "category": {"name": "Entertainment"},
        },
        {
            "id": "rec-2",
            "amount": -1200.00,
            "merchant": {"name": "Landlord"},
            "frequency": "monthly",
            "account": {"displayName": "Checking"},
            "category": {"name": "Housing"},
        },
    ]
}


async def test_recurring_no_dates(mcp_client, mock_monarch_client):
    mock_monarch_client.get_recurring_transactions.return_value = SAMPLE_RECURRING

    result = json.loads(
        (await mcp_client.call_tool("get_recurring_transactions")).content[0].text
    )

    assert len(result["recurringTransactions"]) == 2
    mock_monarch_client.get_recurring_transactions.assert_called_once_with()


async def test_recurring_with_dates(mcp_client, mock_monarch_client):
    mock_monarch_client.get_recurring_transactions.return_value = SAMPLE_RECURRING

    await mcp_client.call_tool(
        "get_recurring_transactions",
        {"start_date": "2025-01-01", "end_date": "2025-12-31"},
    )

    mock_monarch_client.get_recurring_transactions.assert_called_once_with(
        start_date="2025-01-01", end_date="2025-12-31"
    )


async def test_recurring_only_start_error(mcp_client):
    result = json.loads(
        (await mcp_client.call_tool(
            "get_recurring_transactions", {"start_date": "2025-01-01"}
        )).content[0].text
    )
    assert "error" in result


async def test_recurring_only_end_error(mcp_client):
    result = json.loads(
        (await mcp_client.call_tool(
            "get_recurring_transactions", {"end_date": "2025-12-31"}
        )).content[0].text
    )
    assert "error" in result


async def test_recurring_empty(mcp_client, mock_monarch_client):
    mock_monarch_client.get_recurring_transactions.return_value = {
        "recurringTransactions": []
    }

    result = json.loads(
        (await mcp_client.call_tool("get_recurring_transactions")).content[0].text
    )

    assert result["recurringTransactions"] == []


async def test_recurring_error(mcp_client, mock_monarch_client):
    mock_monarch_client.get_recurring_transactions.side_effect = Exception("API down")

    result = (await mcp_client.call_tool("get_recurring_transactions")).content[0].text

    assert "Error" in result
