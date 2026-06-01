"""Tests for transaction-rule tools, Pydantic input models, and helpers."""
# pylint: disable=missing-function-docstring

import json

import pytest
from gql.transport.exceptions import TransportQueryError
from pydantic import ValidationError

from monarch_mcp.transaction_rules import (
    RULE_INPUT_FIELDS,
    CreateTransactionRuleInput,
    UpdateTransactionRuleInput,
    extract_payload_errors,
    normalize_rule,
    rule_to_update_input,
)


# ── Sample fixtures ────────────────────────────────────────────────────


SAMPLE_RULE = {
    "id": "rule-1",
    "order": 1,
    "merchantCriteriaUseOriginalStatement": False,
    "merchantCriteria": None,
    "originalStatementCriteria": [
        {"operator": "eq", "value": "AMZN", "__typename": "RuleStringCriteria"},
    ],
    "merchantNameCriteria": [
        {"operator": "contains", "value": "Amazon",
         "__typename": "RuleStringCriteria"},
    ],
    "amountCriteria": {
        "operator": "gt",
        "isExpense": True,
        "value": 10,
        "valueRange": None,
        "__typename": "RuleAmountCriteria",
    },
    "categoryIds": ["cat-1"],
    "accountIds": ["acct-1"],
    "setMerchantAction": {
        "id": "merchant-1",
        "name": "Amazon",
        "__typename": "Merchant",
    },
    "setCategoryAction": {
        "id": "cat-1",
        "name": "Shopping",
        "icon": ":shopping_cart:",
        "__typename": "Category",
    },
    "addTagsAction": [
        {"id": "tag-1", "name": "online", "color": "#abc",
         "__typename": "TransactionTag"},
        {"id": "tag-2", "name": "review", "color": "#def",
         "__typename": "TransactionTag"},
    ],
    "linkGoalAction": None,
    "linkSavingsGoalAction": None,
    "reviewStatusAction": "reviewed",
    "setHideFromReportsAction": None,
    "recentApplicationCount": 7,
    "lastAppliedAt": "2026-05-01T00:00:00",
    "splitTransactionsAction": None,
    "__typename": "TransactionRuleV2",
}


# ── Pydantic input models ──────────────────────────────────────────────


def test_create_input_serializes_to_camel_case():
    rule = CreateTransactionRuleInput(
        merchant_name_criteria=[{"operator": "contains", "value": "Amazon"}],
        set_category_action="cat-1",
        add_tags_action=["tag-1", "tag-2"],
        apply_to_existing_transactions=True,
    )

    # Snake-case Python fields serialise to Monarch's camelCase; None omitted.
    assert rule.model_dump(by_alias=True, exclude_none=True) == {
        "merchantNameCriteria": [{"operator": "contains", "value": "Amazon"}],
        "setCategoryAction": "cat-1",
        "addTagsAction": ["tag-1", "tag-2"],
        "applyToExistingTransactions": True,
    }


def test_create_input_accepts_camel_case_aliases():
    rule = CreateTransactionRuleInput(**{
        "merchantNameCriteria": [{"operator": "eq", "value": "X"}],
        "setMerchantAction": "New Name",
    })

    assert rule.set_merchant_action == "New Name"
    assert rule.merchant_name_criteria[0].operator == "eq"


def test_create_input_nested_amount_and_splits():
    rule = CreateTransactionRuleInput(
        amount_criteria={
            "operator": "gt", "isExpense": True, "value": 100,
            "valueRange": {"lower": 50, "upper": 150},
        },
        split_transactions_action={
            "amountType": "ABSOLUTE",
            "splitsInfo": [{"categoryId": "c1", "amount": 5}],
        },
    )
    data = rule.model_dump(by_alias=True, exclude_none=True)

    assert data["amountCriteria"]["operator"] == "gt"
    assert data["amountCriteria"]["isExpense"] is True
    assert data["amountCriteria"]["value"] == 100.0
    assert data["amountCriteria"]["valueRange"] == {"lower": 50.0, "upper": 150.0}
    assert data["splitTransactionsAction"] == {
        "amountType": "ABSOLUTE",
        "splitsInfo": [{"categoryId": "c1", "amount": 5.0}],
    }


def test_split_amount_type_rejects_invalid_value():
    # Monarch's API stores an out-of-set amountType silently and then can't
    # serialize it back (this was the live-test failure: 'absolute' lowercase).
    # The model rejects it up front so we never mint an unreadable rule.
    with pytest.raises(ValidationError):
        CreateTransactionRuleInput(
            split_transactions_action={
                "amountType": "absolute",  # not a SplitAmountType — must be ABSOLUTE/PERCENTAGE
                "splitsInfo": [
                    {"categoryId": "c1", "amount": 0.5},
                    {"categoryId": "c2", "amount": 0.5},
                ],
            },
        )


def test_create_input_requires_at_least_one_action():
    with pytest.raises(ValidationError):
        CreateTransactionRuleInput(
            merchant_name_criteria=[{"operator": "contains", "value": "x"}],
        )


def test_create_input_rejects_invalid_operator():
    with pytest.raises(ValidationError):
        CreateTransactionRuleInput(
            merchant_name_criteria=[{"operator": "startswith", "value": "x"}],
            set_category_action="c",
        )


def test_create_input_allows_extra_fields():
    # Forward-compat: exotic/future Monarch fields pass through untouched and
    # satisfy the "needs an action" rule.
    rule = CreateTransactionRuleInput(someFutureAction=True)

    assert rule.model_dump(by_alias=True, exclude_none=True)["someFutureAction"] is True


def test_update_input_dumps_only_set_fields():
    overrides = UpdateTransactionRuleInput(set_category_action="cat-9")

    assert overrides.model_dump(by_alias=True, exclude_unset=True) == {
        "setCategoryAction": "cat-9",
    }


def test_update_input_allows_criteria_only_change():
    # Unlike create, an update may change only criteria (no action required).
    overrides = UpdateTransactionRuleInput(
        merchant_name_criteria=[{"operator": "eq", "value": "y"}],
    )

    assert "merchantNameCriteria" in overrides.model_dump(
        by_alias=True, exclude_unset=True,
    )


# ── rule_to_update_input helper ────────────────────────────────────────


def test_rule_to_update_input_extracts_ids():
    payload = rule_to_update_input(SAMPLE_RULE, {})

    # Plain id strings, not nested objects.
    assert payload["setCategoryAction"] == "cat-1"
    # setMerchantAction is the merchant *name* string.
    assert payload["setMerchantAction"] == "Amazon"
    # addTagsAction is a flat list of ids.
    assert payload["addTagsAction"] == ["tag-1", "tag-2"]


def test_rule_to_update_input_strips_typename():
    payload = rule_to_update_input(SAMPLE_RULE, {})

    assert "__typename" not in json.dumps(payload)


def test_rule_to_update_input_overrides_take_precedence():
    overrides = {
        "setCategoryAction": "cat-overridden",
        "addTagsAction": ["tag-new"],
        "categoryIds": ["cat-x", "cat-y"],
    }

    payload = rule_to_update_input(SAMPLE_RULE, overrides)

    assert payload["setCategoryAction"] == "cat-overridden"
    assert payload["addTagsAction"] == ["tag-new"]
    assert payload["categoryIds"] == ["cat-x", "cat-y"]
    # Untouched fields preserved.
    assert payload["setMerchantAction"] == "Amazon"


def test_rule_to_update_input_preserves_id():
    assert rule_to_update_input(SAMPLE_RULE, {})["id"] == "rule-1"
    assert (
        rule_to_update_input(SAMPLE_RULE, {"setMerchantAction": "Other"})["id"]
        == "rule-1"
    )


# ── normalize_rule ─────────────────────────────────────────────────────


def test_normalize_rule_is_clean_superset():
    out = normalize_rule(SAMPLE_RULE)

    # Backwards-compatible slim keys.
    assert out["id"] == "rule-1"
    assert out["set_category_id"] == "cat-1"
    assert out["set_category_name"] == "Shopping"
    assert out["merchant_name_criteria"] == [{"operator": "contains", "value": "Amazon"}]
    assert out["original_statement_criteria"] == [{"operator": "eq", "value": "AMZN"}]
    # Richer fields.
    assert out["set_merchant_name"] == "Amazon"
    assert out["add_tag_ids"] == ["tag-1", "tag-2"]
    assert out["add_tag_names"] == ["online", "review"]
    assert out["amount_criteria"]["operator"] == "gt"
    assert out["review_status_action"] == "reviewed"
    assert out["recent_application_count"] == 7
    # __typename stripped everywhere.
    assert "__typename" not in json.dumps(out)


# ── extract_payload_errors ─────────────────────────────────────────────


def test_extract_payload_errors_normalises_variants():
    assert extract_payload_errors(
        {"createTransactionRuleV2": {"errors": None}}, "createTransactionRuleV2",
    ) == []
    assert extract_payload_errors(
        {"createTransactionRuleV2": {"errors": {"message": "x"}}},
        "createTransactionRuleV2",
    ) == [{"message": "x"}]
    assert extract_payload_errors(
        {"createTransactionRuleV2": {"errors": [{"message": "a"}]}},
        "createTransactionRuleV2",
    ) == [{"message": "a"}]
    assert extract_payload_errors(None, "createTransactionRuleV2") == []
    assert extract_payload_errors("not-a-dict", "createTransactionRuleV2") == []


# ── MCP tool tests ─────────────────────────────────────────────────────


async def test_get_transaction_rules_returns_normalized_list(mcp_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {"transactionRules": [SAMPLE_RULE]}

    result = json.loads(
        (await mcp_client.call_tool("get_transaction_rules", {})).content[0].text
    )

    assert isinstance(result, list)
    assert result[0]["id"] == "rule-1"
    assert result[0]["set_category_id"] == "cat-1"
    assert result[0]["add_tag_ids"] == ["tag-1", "tag-2"]
    assert "__typename" not in json.dumps(result)
    call_kwargs = mock_monarch_client.gql_call.call_args[1]
    assert call_kwargs["operation"] == "GetTransactionRules"
    assert call_kwargs["variables"] == {}


async def test_create_transaction_rule_sends_camel_input(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {
        "createTransactionRuleV2": {"errors": None},
    }

    result = json.loads(
        (await mcp_write_client.call_tool("create_transaction_rule", {
            "rule": {
                "merchantNameCriteria": [{"operator": "contains", "value": "Test"}],
                "setCategoryAction": "cat-99",
                "addTagsAction": ["tag-7"],
            },
        })).content[0].text
    )

    assert result["created"] is True
    call_kwargs = mock_monarch_client.gql_call.call_args[1]
    assert call_kwargs["operation"] == "Common_CreateTransactionRuleMutationV2"
    sent = call_kwargs["variables"]["input"]
    assert sent["merchantNameCriteria"] == [{"operator": "contains", "value": "Test"}]
    assert sent["setCategoryAction"] == "cat-99"
    assert sent["addTagsAction"] == ["tag-7"]


async def test_create_transaction_rule_surfaces_error_list(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {
        "createTransactionRuleV2": {"errors": [{"message": "bad input"}]},
    }

    result = json.loads(
        (await mcp_write_client.call_tool("create_transaction_rule", {
            "rule": {
                "merchantNameCriteria": [{"operator": "eq", "value": "x"}],
                "setCategoryAction": "c",
            },
        })).content[0].text
    )

    assert result["error"] == "bad input"


async def test_create_transaction_rule_surfaces_error_dict(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {
        "createTransactionRuleV2": {"errors": {"message": "single error"}},
    }

    result = json.loads(
        (await mcp_write_client.call_tool("create_transaction_rule", {
            "rule": {
                "merchantNameCriteria": [{"operator": "eq", "value": "x"}],
                "setCategoryAction": "c",
            },
        })).content[0].text
    )

    assert result["error"] == "single error"


async def test_update_transaction_rule_merges_overrides(mcp_write_client, mock_monarch_client):
    # First call returns the rules list, second returns the update payload.
    mock_monarch_client.gql_call.side_effect = [
        {"transactionRules": [SAMPLE_RULE]},
        {"updateTransactionRuleV2": {"errors": None}},
    ]

    result = json.loads(
        (await mcp_write_client.call_tool("update_transaction_rule", {
            "rule_id": "rule-1",
            "overrides": {"setCategoryAction": "cat-overridden"},
        })).content[0].text
    )

    assert result["updated"] is True
    assert result["rule_id"] == "rule-1"
    assert mock_monarch_client.gql_call.call_count == 2

    update_call_kwargs = mock_monarch_client.gql_call.call_args_list[1][1]
    assert update_call_kwargs["operation"] == "Common_UpdateTransactionRuleMutationV2"
    payload = update_call_kwargs["variables"]["input"]
    assert payload["id"] == "rule-1"
    # Override applied.
    assert payload["setCategoryAction"] == "cat-overridden"
    # Existing fields preserved + normalised (REPLACE-safe merge).
    assert payload["setMerchantAction"] == "Amazon"
    assert payload["addTagsAction"] == ["tag-1", "tag-2"]
    assert payload["categoryIds"] == ["cat-1"]
    assert "__typename" not in json.dumps(payload)
    # Every input-shaped field present in the source rule is carried over.
    for field in RULE_INPUT_FIELDS:
        if field in SAMPLE_RULE:
            assert field in payload


async def test_update_transaction_rule_missing_id_raises(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {"transactionRules": []}

    text = (await mcp_write_client.call_tool("update_transaction_rule", {
        "rule_id": "does-not-exist",
        "overrides": {"setCategoryAction": "c"},
    })).content[0].text

    assert "Error" in text
    assert "does-not-exist" in text


async def test_delete_transaction_rule_returns_clean(mcp_write_client, mock_monarch_client):
    # Server returns deleted: false even on success — must NOT be a failure.
    mock_monarch_client.gql_call.return_value = {
        "deleteTransactionRule": {"deleted": False, "errors": None},
    }

    result = json.loads(
        (await mcp_write_client.call_tool("delete_transaction_rule", {
            "rule_id": "rule-99",
        })).content[0].text
    )

    assert result == {"deleted": True, "rule_id": "rule-99"}
    call_kwargs = mock_monarch_client.gql_call.call_args[1]
    assert call_kwargs["operation"] == "Common_DeleteTransactionRule"
    assert call_kwargs["variables"] == {"id": "rule-99"}


async def test_delete_transaction_rule_surfaces_errors(mcp_write_client, mock_monarch_client):
    mock_monarch_client.gql_call.return_value = {
        "deleteTransactionRule": {"deleted": False, "errors": [{"message": "boom"}]},
    }

    result = json.loads(
        (await mcp_write_client.call_tool("delete_transaction_rule", {
            "rule_id": "x",
        })).content[0].text
    )

    assert result["error"] == "boom"


async def test_write_tools_disabled_in_read_only(mcp_client, mock_monarch_client):  # pylint: disable=unused-argument
    tools = [t.name for t in (await mcp_client.list_tools())]
    assert "create_transaction_rule" not in tools
    assert "update_transaction_rule" not in tools
    assert "delete_transaction_rule" not in tools
    # Read tool stays exposed.
    assert "get_transaction_rules" in tools


# ── partial-data tolerance (field-level GraphQL errors) ────────────────


async def test_get_transaction_rules_tolerates_partial_data(mcp_client, mock_monarch_client):
    # A rule with an unserializable field makes Monarch return partial data
    # alongside errors; gql raises TransportQueryError carrying that data. The
    # tool should use the partial data rather than fail the whole call.
    mock_monarch_client.gql_call.side_effect = TransportQueryError(
        "cannot represent value",
        errors=[{"message": "Enum 'AmountType' cannot represent value"}],
        data={"transactionRules": [SAMPLE_RULE]},
    )

    result = json.loads(
        (await mcp_client.call_tool("get_transaction_rules", {})).content[0].text
    )

    assert isinstance(result, list)
    assert result[0]["id"] == "rule-1"


async def test_get_transaction_rules_propagates_error_without_data(mcp_client, mock_monarch_client):
    # A query error with no data is a real failure → graceful error string.
    mock_monarch_client.gql_call.side_effect = TransportQueryError(
        "hard failure", errors=[{"message": "boom"}],
    )

    text = (await mcp_client.call_tool("get_transaction_rules", {})).content[0].text

    assert "Error getting transaction rules" in text


async def test_update_transaction_rule_tolerates_partial_data(mcp_write_client, mock_monarch_client):
    # The internal fetch hits the same partial-data path; as long as the target
    # rule is present, the update still proceeds.
    mock_monarch_client.gql_call.side_effect = [
        TransportQueryError(
            "cannot represent value",
            errors=[{"message": "Enum 'AmountType' cannot represent value"}],
            data={"transactionRules": [SAMPLE_RULE]},
        ),
        {"updateTransactionRuleV2": {"errors": None}},
    ]

    result = json.loads(
        (await mcp_write_client.call_tool("update_transaction_rule", {
            "rule_id": "rule-1",
            "overrides": {"setCategoryAction": "cat-overridden"},
        })).content[0].text
    )

    assert result["updated"] is True
    payload = mock_monarch_client.gql_call.call_args_list[1][1]["variables"]["input"]
    assert payload["setCategoryAction"] == "cat-overridden"
