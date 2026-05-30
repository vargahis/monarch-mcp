"""Tests for transaction rule tools (create / get / delete)."""
# pylint: disable=missing-function-docstring

import json

from gql.transport.exceptions import TransportQueryError


# ===================================================================
# 1 – happy path: merchant name "contains"
# ===================================================================


async def test_create_rule_merchant_contains(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {
        "createTransactionRuleV2": {"errors": []}
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_rule",
            {
                "set_category_id": "cat-123",
                "merchant_name_value": "Amazon",
            },
        )).content[0].text
    )

    assert result["created"] is True
    call_kwargs = mock_monarch_client.gql_call.call_args[1]
    assert call_kwargs["operation"] == "Common_CreateTransactionRuleMutationV2"
    variables = call_kwargs["variables"]
    assert variables["input"]["merchantNameCriteria"] == [
        {"operator": "contains", "value": "Amazon"}
    ]
    assert variables["input"]["setCategoryAction"] == "cat-123"
    assert variables["input"]["applyToExistingTransactions"] is False


# ===================================================================
# 2 – happy path: merchant name "eq"
# ===================================================================


async def test_create_rule_merchant_eq(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {
        "createTransactionRuleV2": {"errors": []}
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_rule",
            {
                "set_category_id": "cat-456",
                "merchant_name_value": "contribution",
                "merchant_name_operator": "eq",
            },
        )).content[0].text
    )

    assert result["created"] is True
    variables = mock_monarch_client.gql_call.call_args[1]["variables"]
    assert variables["input"]["merchantNameCriteria"] == [
        {"operator": "eq", "value": "contribution"}
    ]


# ===================================================================
# 3 – happy path: original statement criteria
# ===================================================================


async def test_create_rule_original_statement(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {
        "createTransactionRuleV2": {"errors": []}
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_rule",
            {
                "set_category_id": "cat-789",
                "original_statement_value": "ROLLOVER CASH",
                "original_statement_operator": "contains",
            },
        )).content[0].text
    )

    assert result["created"] is True
    variables = mock_monarch_client.gql_call.call_args[1]["variables"]
    assert variables["input"]["originalStatementCriteria"] == [
        {"operator": "contains", "value": "ROLLOVER CASH"}
    ]


# ===================================================================
# 4 – happy path: account_ids scoping
# ===================================================================


async def test_create_rule_with_account_ids(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {
        "createTransactionRuleV2": {"errors": []}
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_rule",
            {
                "set_category_id": "cat-123",
                "merchant_name_value": "Fidelity",
                "account_ids": ["acct-1", "acct-2"],
            },
        )).content[0].text
    )

    assert result["created"] is True
    variables = mock_monarch_client.gql_call.call_args[1]["variables"]
    assert variables["input"]["accountIds"] == ["acct-1", "acct-2"]


# ===================================================================
# 5 – happy path: apply_to_existing_transactions = True
# ===================================================================


async def test_create_rule_apply_to_existing(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {
        "createTransactionRuleV2": {"errors": []}
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_rule",
            {
                "set_category_id": "cat-123",
                "merchant_name_value": "Whole Foods",
                "apply_to_existing_transactions": True,
            },
        )).content[0].text
    )

    assert result["created"] is True
    variables = mock_monarch_client.gql_call.call_args[1]["variables"]
    assert variables["input"]["applyToExistingTransactions"] is True


# ===================================================================
# 6 – validation: no criteria provided
# ===================================================================


async def test_create_rule_no_criteria(mcp_write_client, mock_monarch_client):
    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_rule",
            {"set_category_id": "cat-123"},
        )).content[0].text
    )

    assert "error" in result
    mock_monarch_client.gql_call.assert_not_called()


# ===================================================================
# 7 – validation: invalid merchant_name_operator
# ===================================================================


async def test_create_rule_invalid_merchant_operator(mcp_write_client, mock_monarch_client):
    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_rule",
            {
                "set_category_id": "cat-123",
                "merchant_name_value": "Amazon",
                "merchant_name_operator": "startswith",
            },
        )).content[0].text
    )

    assert "error" in result
    mock_monarch_client.gql_call.assert_not_called()


# ===================================================================
# 8 – validation: invalid original_statement_operator
# ===================================================================


async def test_create_rule_invalid_statement_operator(mcp_write_client, mock_monarch_client):
    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_rule",
            {
                "set_category_id": "cat-123",
                "original_statement_value": "ROLLOVER",
                "original_statement_operator": "regex",
            },
        )).content[0].text
    )

    assert "error" in result
    mock_monarch_client.gql_call.assert_not_called()


# ===================================================================
# 9 – API-level error: errors as list
# ===================================================================


async def test_create_rule_api_error_list(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {
        "createTransactionRuleV2": {
            "errors": [{"message": "Category not found"}]
        }
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_rule",
            {
                "set_category_id": "cat-bad",
                "merchant_name_value": "Amazon",
            },
        )).content[0].text
    )

    assert "error" in result
    assert "Category not found" in result["error"]


# ===================================================================
# 9b – API-level error: errors as bare dict (Monarch's actual shape)
# ===================================================================


async def test_create_rule_api_error_dict(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {
        "createTransactionRuleV2": {
            "errors": {"message": "Invalid operator"}
        }
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_rule",
            {
                "set_category_id": "cat-123",
                "merchant_name_value": "Amazon",
                "merchant_name_operator": "contains",
            },
        )).content[0].text
    )

    assert "error" in result
    assert "Invalid operator" in result["error"]


# ===================================================================
# 10 – transport error handled by decorator
# ===================================================================


async def test_create_rule_transport_error(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.side_effect = Exception("Network failure")

    result = (await mcp_write_client.call_tool(
        "create_transaction_rule",
        {
            "set_category_id": "cat-123",
            "merchant_name_value": "Amazon",
        },
    )).content[0].text

    assert "Error" in result
    assert "Network failure" in result


# ===================================================================
# 11 – both merchant name and original statement provided together
# ===================================================================


async def test_create_rule_both_criteria(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {
        "createTransactionRuleV2": {"errors": []}
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction_rule",
            {
                "set_category_id": "cat-123",
                "merchant_name_value": "Fidelity",
                "original_statement_value": "ROLLOVER CASH",
            },
        )).content[0].text
    )

    assert result["created"] is True
    variables = mock_monarch_client.gql_call.call_args[1]["variables"]
    assert "merchantNameCriteria" in variables["input"]
    assert "originalStatementCriteria" in variables["input"]


# ===================================================================
# 12 – get_transaction_rules: slimmed shape
# ===================================================================


async def test_get_rules_slim_shape(mcp_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {
        "transactionRules": [
            {
                "id": "rule-1",
                "merchantNameCriteria": [{"operator": "contains", "value": "amazon"}],
                "originalStatementCriteria": None,
                "setCategoryAction": {"id": "cat-1", "name": "Shopping"},
            },
            {
                "id": "rule-2",
                "merchantNameCriteria": None,
                "originalStatementCriteria": [{"operator": "eq", "value": "rollover"}],
                "setCategoryAction": {"id": "cat-2", "name": "Transfer"},
            },
        ]
    }

    result = json.loads(
        (await mcp_client.call_tool("get_transaction_rules")).content[0].text
    )

    assert mock_monarch_client.gql_call.call_args[1]["operation"] == "Common_GetTransactionRules"
    assert result == [
        {
            "id": "rule-1",
            "set_category_id": "cat-1",
            "set_category_name": "Shopping",
            "merchant_name_criteria": [{"operator": "contains", "value": "amazon"}],
            "original_statement_criteria": [],
        },
        {
            "id": "rule-2",
            "set_category_id": "cat-2",
            "set_category_name": "Transfer",
            "merchant_name_criteria": [],
            "original_statement_criteria": [{"operator": "eq", "value": "rollover"}],
        },
    ]


# ===================================================================
# 13 – get_transaction_rules: empty list
# ===================================================================


async def test_get_rules_empty(mcp_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {"transactionRules": []}

    result = json.loads(
        (await mcp_client.call_tool("get_transaction_rules")).content[0].text
    )

    assert result == []


# ===================================================================
# 14 – delete_transaction_rule: happy path
# ===================================================================


async def test_delete_rule_success(mcp_write_client, mock_monarch_client):
    # Monarch's payload `deleted` field is unreliable; a successful call (no
    # exception) means the rule was deleted, so the tool reports deleted: true.
    mock_monarch_client.gql_call.return_value = {
        "deleteTransactionRule": {"__typename": "DeleteTransactionRuleMutation"}
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "delete_transaction_rule", {"rule_id": "rule-1"}
        )).content[0].text
    )

    assert result == {"deleted": True, "rule_id": "rule-1"}
    call_kwargs = mock_monarch_client.gql_call.call_args[1]
    assert call_kwargs["operation"] == "Common_DeleteTransactionRuleMutation"
    assert call_kwargs["variables"] == {"id": "rule-1"}


# ===================================================================
# 15 – delete_transaction_rule: not-found / transport error via decorator
# ===================================================================


async def test_delete_rule_not_found(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.side_effect = TransportQueryError("Not found")

    result = (await mcp_write_client.call_tool(
        "delete_transaction_rule", {"rule_id": "does-not-exist"}
    )).content[0].text

    assert "Error" in result
    assert "Not found" in result
