"""Tests for account management tools: create, update, delete, history, snapshots."""
# pylint: disable=missing-function-docstring

import json


# ===================================================================
# create_manual_account
# ===================================================================


async def test_create_account_happy(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_manual_account.return_value = {
        "createManualAccount": {"id": "acc-new", "displayName": "Savings"}
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_manual_account",
            {
                "account_name": "Savings",
                "account_type": "depository",
                "account_sub_type": "savings",
                "is_in_net_worth": True,
                "account_balance": 1000.0,
            },
        )).content[0].text
    )

    assert result["createManualAccount"]["id"] == "acc-new"
    mock_monarch_client.create_manual_account.assert_called_once_with(
        account_type="depository",
        account_sub_type="savings",
        is_in_net_worth=True,
        account_name="Savings",
        account_balance=1000.0,
    )


async def test_create_account_default_balance(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_manual_account.return_value = {
        "createManualAccount": {"id": "acc-new"}
    }

    await mcp_write_client.call_tool(
        "create_manual_account",
        {
            "account_name": "Test",
            "account_type": "loan",
            "account_sub_type": "personal",
            "is_in_net_worth": False,
        },
    )

    call_kwargs = mock_monarch_client.create_manual_account.call_args[1]
    assert call_kwargs["account_balance"] == 0


async def test_create_account_error(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_manual_account.side_effect = Exception(
        "Invalid type"
    )

    result = (await mcp_write_client.call_tool(
        "create_manual_account",
        {
            "account_name": "Bad",
            "account_type": "invalid",
            "account_sub_type": "bad",
            "is_in_net_worth": True,
        },
    )).content[0].text

    assert "Error" in result


# ===================================================================
# update_account
# ===================================================================


async def test_update_account_name(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_account.return_value = {
        "id": "acc-1",
        "displayName": "New Name",
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "update_account", {"account_id": "acc-1", "account_name": "New Name"}
        )).content[0].text
    )

    assert result["displayName"] == "New Name"
    call_kwargs = mock_monarch_client.update_account.call_args[1]
    assert call_kwargs["account_id"] == "acc-1"
    assert call_kwargs["account_name"] == "New Name"


async def test_update_account_balance(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_account.return_value = {
        "id": "acc-1",
        "currentBalance": 5000.0,
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "update_account", {"account_id": "acc-1", "account_balance": 5000.0}
        )).content[0].text
    )

    assert result["currentBalance"] == 5000.0


async def test_update_account_noop(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_account.return_value = {"id": "acc-1"}

    result = json.loads(
        (await mcp_write_client.call_tool(
            "update_account", {"account_id": "acc-1"}
        )).content[0].text
    )

    assert result["id"] == "acc-1"
    call_kwargs = mock_monarch_client.update_account.call_args[1]
    assert call_kwargs == {"account_id": "acc-1"}


async def test_update_account_multi_field(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_account.return_value = {"id": "acc-1"}

    await mcp_write_client.call_tool(
        "update_account",
        {
            "account_id": "acc-1",
            "account_name": "Updated",
            "include_in_net_worth": False,
            "hide_from_summary_list": True,
        },
    )

    call_kwargs = mock_monarch_client.update_account.call_args[1]
    assert call_kwargs["account_name"] == "Updated"
    assert call_kwargs["include_in_net_worth"] is False
    assert call_kwargs["hide_from_summary_list"] is True


async def test_update_account_error(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_account.side_effect = Exception("Not found")

    result = (await mcp_write_client.call_tool(
        "update_account", {"account_id": "bad-id", "account_name": "X"}
    )).content[0].text

    assert "Error" in result


# ===================================================================
# delete_account
# ===================================================================


async def test_delete_account_happy(mcp_write_client, mock_monarch_client):
    mock_monarch_client.delete_account.return_value = None

    result = json.loads(
        (await mcp_write_client.call_tool(
            "delete_account", {"account_id": "acc-1"}
        )).content[0].text
    )

    assert result["deleted"] is True
    assert result["account_id"] == "acc-1"
    assert result["result"] is None
    mock_monarch_client.delete_account.assert_called_once_with("acc-1")


async def test_delete_account_error(mcp_write_client, mock_monarch_client):
    mock_monarch_client.delete_account.side_effect = Exception("Account not found")

    result = (await mcp_write_client.call_tool(
        "delete_account", {"account_id": "bad-id"}
    )).content[0].text

    assert "Error" in result


# ===================================================================
# get_account_history
# ===================================================================


async def test_account_history_happy(mcp_client, mock_monarch_client):
    mock_monarch_client.get_account_history.return_value = {
        "accountHistory": [
            {"date": "2025-01-01", "balance": 1000},
            {"date": "2025-01-02", "balance": 1050},
        ]
    }

    result = json.loads(
        (await mcp_client.call_tool(
            "get_account_history", {"account_id": "acc-1"}
        )).content[0].text
    )

    assert len(result["accountHistory"]) == 2
    mock_monarch_client.get_account_history.assert_called_once_with("acc-1")


async def test_account_history_error(mcp_client, mock_monarch_client):
    mock_monarch_client.get_account_history.side_effect = Exception("Not found")

    result = (await mcp_client.call_tool(
        "get_account_history", {"account_id": "bad-id"}
    )).content[0].text

    assert "Error" in result


# ===================================================================
# get_recent_account_balances
# ===================================================================


async def test_recent_balances_no_date(mcp_client, mock_monarch_client):
    mock_monarch_client.get_recent_account_balances.return_value = {
        "recentAccountBalances": []
    }

    await mcp_client.call_tool("get_recent_account_balances")

    mock_monarch_client.get_recent_account_balances.assert_called_once_with()


async def test_recent_balances_with_date(mcp_client, mock_monarch_client):
    mock_monarch_client.get_recent_account_balances.return_value = {
        "recentAccountBalances": [{"date": "2025-01-01", "balance": 1000}]
    }

    await mcp_client.call_tool(
        "get_recent_account_balances", {"start_date": "2025-01-01"}
    )

    mock_monarch_client.get_recent_account_balances.assert_called_once_with(
        start_date="2025-01-01"
    )


# ===================================================================
# get_account_snapshots_by_type
# ===================================================================


async def test_snapshots_by_type_month(mcp_client, mock_monarch_client):
    mock_monarch_client.get_account_snapshots_by_type.return_value = {
        "snapshots": []
    }

    await mcp_client.call_tool(
        "get_account_snapshots_by_type",
        {"start_date": "2025-01-01", "timeframe": "month"},
    )

    mock_monarch_client.get_account_snapshots_by_type.assert_called_once_with(
        "2025-01-01", "month"
    )


async def test_snapshots_by_type_year(mcp_client, mock_monarch_client):
    mock_monarch_client.get_account_snapshots_by_type.return_value = {
        "snapshots": []
    }

    await mcp_client.call_tool(
        "get_account_snapshots_by_type",
        {"start_date": "2020-01-01", "timeframe": "year"},
    )

    mock_monarch_client.get_account_snapshots_by_type.assert_called_once_with(
        "2020-01-01", "year"
    )


async def test_snapshots_by_type_invalid_timeframe(mcp_client):
    result = json.loads(
        (await mcp_client.call_tool(
            "get_account_snapshots_by_type",
            {"start_date": "2025-01-01", "timeframe": "week"},
        )).content[0].text
    )
    assert "error" in result


# ===================================================================
# get_aggregate_snapshots
# ===================================================================


async def test_aggregate_snapshots_no_params(mcp_client, mock_monarch_client):
    mock_monarch_client.get_aggregate_snapshots.return_value = {"snapshots": []}

    await mcp_client.call_tool("get_aggregate_snapshots")

    mock_monarch_client.get_aggregate_snapshots.assert_called_once_with()


async def test_aggregate_snapshots_with_dates(mcp_client, mock_monarch_client):
    mock_monarch_client.get_aggregate_snapshots.return_value = {"snapshots": []}

    await mcp_client.call_tool(
        "get_aggregate_snapshots",
        {"start_date": "2025-01-01", "end_date": "2025-12-31"},
    )

    mock_monarch_client.get_aggregate_snapshots.assert_called_once_with(
        start_date="2025-01-01", end_date="2025-12-31"
    )


async def test_aggregate_snapshots_with_type(mcp_client, mock_monarch_client):
    mock_monarch_client.get_aggregate_snapshots.return_value = {"snapshots": []}

    await mcp_client.call_tool(
        "get_aggregate_snapshots", {"account_type": "depository"}
    )

    mock_monarch_client.get_aggregate_snapshots.assert_called_once_with(
        account_type="depository"
    )


# ===================================================================
# get_account_type_options
# ===================================================================


async def test_account_type_options_happy(mcp_client, mock_monarch_client):
    mock_monarch_client.get_account_type_options.return_value = {
        "accountTypeOptions": [
            {"type": "depository", "subTypes": ["checking", "savings"]},
        ]
    }

    result = json.loads(
        (await mcp_client.call_tool("get_account_type_options")).content[0].text
    )

    assert len(result["accountTypeOptions"]) == 1
    mock_monarch_client.get_account_type_options.assert_called_once()


# ===================================================================
# get_credit_history
# ===================================================================


async def test_credit_history_happy(mcp_client, mock_monarch_client):
    mock_monarch_client.get_credit_history.return_value = {
        "creditHistory": [{"date": "2025-01-01", "score": 750}]
    }

    result = json.loads(
        (await mcp_client.call_tool("get_credit_history")).content[0].text
    )

    assert result["creditHistory"][0]["score"] == 750
    mock_monarch_client.get_credit_history.assert_called_once()


async def test_credit_history_empty(mcp_client, mock_monarch_client):
    mock_monarch_client.get_credit_history.return_value = {"creditHistory": []}

    result = json.loads(
        (await mcp_client.call_tool("get_credit_history")).content[0].text
    )

    assert result["creditHistory"] == []
