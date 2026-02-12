# TODO: Test and Fix MCP Tools

Track progress across sessions. Update checkboxes as work proceeds.

## Phase 1: Confirm Critical Crashes
- [x] TEST 1.1 — Bug A CONFIRMED: `create_transaction() got an unexpected keyword argument 'description'`
- [x] TEST 1.2 — Bug B CONFIRMED: `request_accounts_refresh() missing 1 required positional argument: 'account_ids'`
- [x] TEST 1.3 — Bug C CONFIRMED: `get_transaction_tags` returns `[]` (wrong key: reads `tags` instead of `householdTransactionTags`)
- [x] TEST 1.4 — Bug D CONFIRMED: `get_budgets` returns `[]` (wrong key: reads `budgets` instead of `budgetData`)

## Phase 2: Verify Working Read Operations
- [x] TEST 2.1 — `get_accounts` PASS: 30 accounts returned, all fields populated, all `is_active: true`
- [x] TEST 2.2 — `get_transactions` PASS (10 txns returned). Bug H CONFIRMED: `is_pending` always false despite `pending: true` in API. Bug I CONFIRMED: `description` always null (field doesn't exist in GraphQL)
- [x] TEST 2.3 — `get_transactions` with date range PASS: Jan 2025, 100 txns, all dates in range
- [x] TEST 2.4 — `get_cashflow` PASS: returns `byCategory`, `byCategoryGroup`, `byMerchant`, `summary` keys correctly
- [x] TEST 2.5 — `get_account_holdings` PASS: E*Trade MSCI account shows 335 shares MSCI stock

## Phase 3: Confirm Conditional Failures
- [x] TEST 3.1 — Bug E CONFIRMED: `got an unexpected keyword argument 'account_id'. Did you mean 'account_ids'?`
- [x] TEST 3.2 — Bug F CONFIRMED: `You must specify both a startDate and endDate`
- [x] TEST 3.3 — Bug F CONFIRMED (end_date only): same error
- [x] TEST 3.4 — Bug G CONFIRMED: `You must specify both a startDate and endDate`

## Phase 4: Verify Write Operations
- [x] TEST 4.1 — `update_transaction` notes PASS. Also CONFIRMED Bug H: response shows `pending: true` but get_transactions reports `is_pending: false`
- [x] TEST 4.2 — `update_transaction` no-op PASS: succeeds with no changes
- [x] TEST 4.3 — `update_transaction` invalid ID PASS: GraphQL error returned gracefully
- [x] TEST 4.4 — `create_transaction_tag` PASS: tag created (id: 235544574544723947, name: MCP-Test-Tag)
- [x] TEST 4.5 — `create_transaction_tag` bad color PASS: validation caught (`"Invalid color format..."`)
- [x] TEST 4.6 — `create_transaction_tag` empty name PASS: validation caught (`"Tag name cannot be empty"`)
- [x] TEST 4.7 — `set_transaction_tags` apply PASS: tag applied to transaction
- [x] TEST 4.8 — `set_transaction_tags` remove PASS: empty list removes all tags

## Phase 5: Edge Cases and Boundary Testing
- [x] TEST 5.1 — Pagination PASS: page 1 and page 2 have no overlapping IDs
- [x] TEST 5.2 — Large offset PASS: returns `[]`
- [x] TEST 5.3 — limit=0: returns empty error message `"Error getting transactions: "` (minor: unhelpful message)
- [x] TEST 5.4 — Invalid date format: GraphQL error caught gracefully `"Something went wrong while processing: None"`
- [x] TEST 5.5 — Future dates PASS: returns `[]`
- [x] TEST 5.6 — Holdings for checking account PASS: returns empty edges `[]`
- [x] TEST 5.7 — Holdings for invalid ID PASS: GraphQL error returned gracefully
- [x] TEST 5.8 — 3-digit hex color PASS: validation caught
- [x] TEST 5.9 — Whitespace-only name PASS: validation caught
- [x] TEST 5.10 — Duplicate tag name: API rejects with `"A tag with this name already exists."` (no MCP-level check needed)

## Phase 6: Authentication
- [x] TEST 6.1 — `check_auth_status` PASS: "Authentication token found in secure keyring storage"
- [x] TEST 6.2 — `debug_session_loading` PASS: "Token found in keyring (length: 64)"
- [x] TEST 6.3 — `setup_authentication` PASS: returns instruction text

## Cleanup
- [x] Revert modified transactions (notes reverted to empty)
- [ ] Delete test tag "MCP-Test-Tag" via Monarch web UI
- [x] Remove test tags from transactions (removed via `set_transaction_tags` empty list)

---

## Bug Fixes (after test confirmation)
- [ ] Fix Bug A — `create_transaction`: wrong params, missing required args
- [ ] Fix Bug B — `refresh_accounts`: missing required `account_ids` arg
- [ ] Fix Bug C — `get_transaction_tags`: wrong response key (`householdTransactionTags`)
- [ ] Fix Bug D — `get_budgets`: wrong response key + wrong data model
- [ ] Fix Bug E — `get_transactions` account filter: `account_id` -> `account_ids` (list)
- [ ] Fix Bug F — `get_transactions` single date: validate both dates required
- [ ] Fix Bug G — `get_cashflow` single date: validate both dates required
- [ ] Fix Bug H — `get_transactions` `is_pending`: field name `pending` not `isPending`
- [ ] Fix Bug I — `get_transactions` `description`: field doesn't exist in GraphQL response
- [ ] Fix Bug J — `create_transaction` vs `update_transaction` truthiness inconsistency
- [ ] Fix Bug K — Remove dead `MonarchConfig` class

## Unit Tests (after all fixes)
- [ ] Design unit test architecture (mocking strategy, fixtures)
- [ ] Write unit tests for all tools
- [ ] Verify tests pass
