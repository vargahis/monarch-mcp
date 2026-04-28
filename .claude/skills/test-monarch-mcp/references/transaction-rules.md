# Phase 13 — Transaction Rules (7 tests)

> **Read-only mode:** Skip entire phase (0 tests). All tests require write tools.

> ⚠️ **No cleanup possible**: Monarch has no delete-rule API. Rules created here persist in the
> account. All test rules use merchant/statement values prefixed with `MCP-Test-` for easy
> manual identification and deletion via the Monarch UI.

Use `{valid_category_id}` from discovery for all `set_category_id` arguments.

## 13.1 — create_transaction_rule: merchant name match (contains)
Call `create_transaction_rule(set_category_id={valid_category_id}, merchant_name_value="MCP-Test-Merchant")`.
**Expected:** JSON with `created: true`.

## 13.2 — create_transaction_rule: original statement match
Call `create_transaction_rule(set_category_id={valid_category_id}, original_statement_value="MCP-Test-Statement")`.
**Expected:** JSON with `created: true`.

## 13.3 — create_transaction_rule: both conditions
Call `create_transaction_rule(set_category_id={valid_category_id}, merchant_name_value="MCP-Test-Both", original_statement_value="MCP-Test-Both-Stmt")`.
**Expected:** JSON with `created: true`.

## 13.4 — create_transaction_rule: exact match operator
Call `create_transaction_rule(set_category_id={valid_category_id}, merchant_name_value="MCP-Test-Exact", merchant_name_operator="eq")`.
**Expected:** JSON with `created: true`.

## 13.5 — create_transaction_rule: apply_to_existing_transactions
Call `create_transaction_rule(set_category_id={valid_category_id}, merchant_name_value="MCP-Test-Backfill", apply_to_existing_transactions=True)`.
**Expected:** JSON with `created: true`.

## 13.6 — create_transaction_rule: validation — neither condition provided
Call `create_transaction_rule(set_category_id={valid_category_id})`.
**Expected:** JSON with an `error` key indicating at least one of `merchant_name_value` or `original_statement_value` is required.

## 13.7 — create_transaction_rule: validation — invalid operator
Call `create_transaction_rule(set_category_id={valid_category_id}, merchant_name_value="MCP-Test-Op", merchant_name_operator="regex")`.
**Expected:** JSON with an `error` key indicating `merchant_name_operator` must be `contains` or `eq`.
