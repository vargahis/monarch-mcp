# Phase 13 — Transaction Rules (10 tests)

> **Read-only mode:** Run test 13.6 only (`get_transaction_rules`). Skip the rest (create/update/
> delete require write tools).

> **Scope:** This phase checks that the agent can **author the rule schema accurately** from intent
> — choosing the right criteria and actions and structuring the nested shapes — across the full
> surface (category, tag, merchant-rename, amount, split), then **verifies the result by reading it
> back** with `get_transaction_rules`. Plus the REPLACE-safe update, one graceful error, and cleanup.
> Deterministic input validation (operator enums, "needs an action") is covered by the mocked unit
> tests, so it is not repeated here.

**How to author:** `create_transaction_rule`/`update_transaction_rule` take a typed rule object whose
fields are visible in the tool schema (Monarch's camelCase names — `merchantNameCriteria`,
`setCategoryAction`, `addTagsAction`, `setMerchantAction`, `amountCriteria`,
`splitTransactionsAction`, …). Build the object from the intent below; do **not** expect the exact
JSON to be dictated to you — that is what is being tested.

Use `{valid_category_id}` from discovery wherever a category is needed.

> **Note:** Monarch **lowercases** rule criteria *values*, so a rule created to match
> `MCP-Test-Rule-Cat` reads back as `mcp-test-rule-cat`. Match case-insensitively when locating test
> rules and when checking action values.

> ✅ **Cleanup:** `get_transaction_rules` lists rule IDs and `delete_transaction_rule` removes them.
> Cleanup deletes every rule whose criteria value contains `mcp-test` (case-insensitive) and the
> `MCP-Test-` tag created in 13.2.

## 13.1 — Author a category rule
Create a rule that assigns category `{valid_category_id}` to transactions whose merchant name
contains `MCP-Test-Rule-Cat`.
**Expected:** JSON with `created: true`. (Agent must use a merchant-name criterion + a set-category
action.)

## 13.2 — Author a tagging rule (action that takes an id)
First create a tag: `create_transaction_tag(name="MCP-Test-Rule-Tag", color="#19D2A5")` and keep its
id as `{created_tag_id}`. Then create a rule that assigns category `{valid_category_id}` **and** adds
tag `{created_tag_id}` to transactions whose merchant name contains `MCP-Test-Rule-Tag-Match`.
**Expected:** JSON with `created: true`. (Agent must put the tag **id** in the add-tags action, not
the tag name.)

## 13.3 — Author a merchant-rename rule (action that takes a name)
Create a rule that renames the merchant to `MCP-Test-Renamed-Merchant` for transactions whose
merchant name contains `MCP-Test-Rule-Rename`.
**Expected:** JSON with `created: true`. (Agent must use the set-merchant action with the **name
string**.)

## 13.4 — Author an amount rule (nested criterion)
Create a rule that assigns category `{valid_category_id}` to **expense** transactions **over 100**
whose merchant name contains `MCP-Test-Rule-Amount`.
**Expected:** JSON with `created: true` **or** a graceful `{ "error": ... }` (the exact amount
operator enum varies by account — a clean error is acceptable, a crash/`Traceback` is not). If
created, 13.6 will confirm the amount criterion is present.

## 13.5 — Author a split rule (deep nested action)
Create a rule that **splits** transactions whose merchant name contains `MCP-Test-Rule-Split` into
two equal legs, both categorized as `{valid_category_id}`.
**Expected:** JSON with `created: true` **or** a graceful `{ "error": ... }` (the split amount-type
enum varies by account; a clean error is acceptable, a crash is not). If created, 13.6 will confirm
the split action is present.

## 13.6 — get_transaction_rules: verify what was authored
Call `get_transaction_rules()`.
**Expected:** A JSON array. Each item is the normalized shape: `id`, `set_category_id`,
`set_category_name`, `merchant_name_criteria`, `original_statement_criteria`, plus richer keys
(`add_tag_ids`, `set_merchant_name`, `amount_criteria`, `split_transactions_action`,
`recent_application_count`). **Record the `id`** of every rule whose criteria value contains
`mcp-test`.

In **write mode**, confirm the rules authored above came out correctly (criteria values lowercased):
- 13.1 rule: `set_category_id == {valid_category_id}`.
- 13.2 rule: `add_tag_ids` contains `{created_tag_id}`.
- 13.3 rule: `set_merchant_name` equals `MCP-Test-Renamed-Merchant` (case-insensitive).
- 13.4 rule (if created): `amount_criteria` is present/non-null.
- 13.5 rule (if created): `split_transactions_action` is present/non-null.

A mismatch here (e.g. the tag rule shows no `add_tag_ids`, or the tag *name* instead of its id) is a
**FAIL** — it means the agent mis-authored the schema.

> In **read-only mode**, run only this test and stop: no rules were created, so just verify the call
> returns a JSON list with the expected keys and no error.

## 13.7 — update_transaction_rule: REPLACE-safe partial update
Take the tag rule from 13.2 (by its recorded id). Update **only** its merchant-name match to contain
`MCP-Test-Rule-Updated`, changing nothing else — pass just that one field in `overrides`.
**Expected:** JSON with `updated: true`. Then call `get_transaction_rules` again and confirm that
rule now has the new merchant criterion **and still** has `set_category_id == {valid_category_id}` and
`add_tag_ids` containing `{created_tag_id}`. (Proves the agent passed a minimal override and the tool
preserved the rest despite Monarch's replace semantics.)

## 13.8 — delete_transaction_rule: happy path
Pick one `mcp-test` rule id. Call `delete_transaction_rule(rule_id={that_id})`.
**Expected:** JSON `{ "deleted": true, "rule_id": "{that_id}" }`.

## 13.9 — update_transaction_rule: invalid id (graceful)
Call `update_transaction_rule(rule_id="000000000000000000", overrides={...any one field...})`.
**Expected:** A graceful `Error ...` string (the id is not found). No crash/`Traceback`.

## 13.10 — cleanup verification
Delete every remaining `mcp-test` rule and the `MCP-Test-Rule-Tag` tag from 13.2. Call
`get_transaction_rules()` again and confirm **zero** rules with `mcp-test` criteria remain. The
account should be back to its pre-test rule set.
