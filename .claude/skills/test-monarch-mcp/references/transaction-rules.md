# Phase 13 — Transaction Rules (11 tests)

> **Read-only mode:** Run test 13.8 only (`get_transaction_rules`). Skip the rest (create/delete
> require write tools).

Use `{valid_category_id}` from discovery for all `set_category_id` arguments.

> **Note:** Monarch **lowercases** rule criteria values, so a rule created with merchant value
> `MCP-Test-Merchant` is stored and returned as `mcp-test-merchant`. Match case-insensitively when
> identifying test rules.

> ✅ **Cleanup IS possible** (as of the rule-management tools): `get_transaction_rules` lists rule
> IDs and `delete_transaction_rule` removes them. The cleanup phase deletes every rule whose
> criteria value contains `mcp-test` (case-insensitive).

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

## 13.8 — get_transaction_rules: lists rules (incl. created ones)
Call `get_transaction_rules()`.
**Expected:** A JSON array. Each item has `id`, `set_category_id`, `set_category_name`,
`merchant_name_criteria`, and `original_statement_criteria`. The rules created in 13.1–13.5 appear,
with criteria values lowercased (e.g. `mcp-test-merchant`). **Record the IDs** of every rule whose
criteria value contains `mcp-test` (case-insensitive) — used for 13.9 and cleanup.

> In read-only mode, run only this test and stop after it (no rules were created to assert on; just
> verify the call returns a list without error).

## 13.9 — delete_transaction_rule: happy path
Pick one `mcp-test` rule ID from 13.8. Call `delete_transaction_rule(rule_id={that_id})`.
**Expected:** JSON `{ "deleted": true, "rule_id": "{that_id}" }`.

## 13.10 — delete_transaction_rule: invalid ID
Call `delete_transaction_rule(rule_id="000000000000000000")`.
**Expected:** A graceful error string (Monarch returns "Not found"). No crash.

## 13.11 — cleanup verification
Call `get_transaction_rules()` again and confirm **zero** rules with `mcp-test` criteria remain
(the cleanup phase deletes any still present). The account should be back to its pre-test rule set.
