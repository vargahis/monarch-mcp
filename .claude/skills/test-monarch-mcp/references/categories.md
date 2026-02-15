# Phase 8 — Categories (10 tests)

> **Read-only mode:** Run tests 8.1-8.3 only. Skip 8.4-8.10 (create/delete category requires write mode).

## 8.1 — get_transaction_categories: returns categories
Call `get_transaction_categories()`.
**Expected:** JSON with a `categories` key containing a non-empty list. Each category has `id`, `name`, and `group`.

## 8.2 — get_transaction_category_groups: returns groups
Call `get_transaction_category_groups()`.
**Expected:** JSON with a `categoryGroups` key containing a non-empty list. Each group has `id`, `name`, `type`.

## 8.3 — get_transaction_category_groups: groups have type field
From the result of 8.2, verify at least one group has `type` equal to `"expense"` or `"income"`.

## 8.4 — create_transaction_category: happy path
Pick a `group_id` from a group with `type: "expense"` discovered in 8.2.
Call `create_transaction_category(group_id={group_id}, name="MCP-Test-Category")`.
**Expected:** JSON response with the created category. Record the ID in `created_resources.categories`.

## 8.5 — create_transaction_category: custom icon
Call `create_transaction_category(group_id={group_id}, name="MCP-Test-Icon-Cat", icon="🎮")`.
**Expected:** Success. Record the ID.

## 8.6 — create_transaction_category: with rollover
Call `create_transaction_category(group_id={group_id}, name="MCP-Test-Rollover", rollover_enabled=True, rollover_start_month="2025-01-01")`.
**Expected:** Success. Record the ID.

## 8.7 — create_transaction_category: invalid group_id
Call `create_transaction_category(group_id="invalid-group", name="MCP-Test-Bad")`.
**Expected:** Error response.

## 8.8 — get_transaction_categories: created categories visible
Call `get_transaction_categories()` and verify the categories created in 8.4–8.6 appear in the list.

## 8.9 — delete_transaction_category: happy path
Call `delete_transaction_category(category_id={id from 8.5})`.
**Expected:** JSON with `deleted: true`. Remove from `created_resources.categories`.

## 8.10 — delete_transaction_category: invalid ID
Call `delete_transaction_category(category_id="invalid-cat-id")`.
**Expected:** Error response.
