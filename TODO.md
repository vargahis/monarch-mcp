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
- [ ] TEST 2.6 — `get_budgets` happy path (both dates)
- [ ] TEST 2.7 — `get_budgets` happy path (no dates — defaults)
- [ ] TEST 2.8 — `get_cashflow` happy path (no dates — defaults)

## Phase 3: Confirm Conditional Failures
- [x] TEST 3.1 — Bug E CONFIRMED: `got an unexpected keyword argument 'account_id'. Did you mean 'account_ids'?`
- [x] TEST 3.2 — Bug F CONFIRMED: `You must specify both a startDate and endDate`
- [x] TEST 3.3 — Bug F CONFIRMED (end_date only): same error
- [x] TEST 3.4 — Bug G CONFIRMED: `You must specify both a startDate and endDate`
- [x] TEST 3.5 — Bug L CONFIRMED: `get_budgets(start_date=...)` → `"Error getting budgets: You must specify both a startDate and endDate, not just one of them."` (no client-side validation)
- [x] TEST 3.6 — Bug L CONFIRMED (end_date only): same error
- [ ] TEST 3.7 — `get_cashflow` with only `end_date` (Bug G variant)

## Phase 4: Verify Write Operations
- [x] TEST 4.1 — `update_transaction` notes PASS. Also CONFIRMED Bug H: response shows `pending: true` but get_transactions reports `is_pending: false`
- [x] TEST 4.2 — `update_transaction` no-op PASS: succeeds with no changes
- [x] TEST 4.3 — `update_transaction` invalid ID PASS: GraphQL error returned gracefully
- [x] TEST 4.4 — `create_transaction_tag` PASS: tag created (id: 235544574544723947, name: MCP-Test-Tag)
- [x] TEST 4.5 — `create_transaction_tag` bad color PASS: validation caught (`"Invalid color format..."`)
- [x] TEST 4.6 — `create_transaction_tag` empty name PASS: validation caught (`"Tag name cannot be empty"`)
- [x] TEST 4.7 — `set_transaction_tags` apply PASS: tag applied to transaction
- [x] TEST 4.8 — `set_transaction_tags` remove PASS: empty list removes all tags
- [ ] TEST 4.9 — `create_transaction` happy path (post-fix, with notes)
- [ ] TEST 4.10 — `create_transaction` positive amount (income)
- [ ] TEST 4.11 — `create_transaction` without optional `notes`
- [ ] TEST 4.12 — `create_transaction` invalid account_id
- [ ] TEST 4.13 — `create_transaction` invalid category_id
- [ ] TEST 4.14 — `create_transaction` invalid date format
- [ ] TEST 4.15 — `create_transaction` amount=0
- [ ] TEST 4.16 — `update_transaction` update amount
- [ ] TEST 4.17 — `update_transaction` update merchant_name
- [ ] TEST 4.18 — `update_transaction` update date
- [ ] TEST 4.19 — `update_transaction` toggle hide_from_reports
- [ ] TEST 4.20 — `update_transaction` toggle needs_review
- [ ] TEST 4.21 — `update_transaction` update multiple fields at once
- [ ] TEST 4.22 — `update_transaction` update category_id
- [ ] TEST 4.23 — `set_transaction_tags` apply multiple tags
- [ ] TEST 4.24 — `set_transaction_tags` invalid transaction_id
- [ ] TEST 4.25 — `set_transaction_tags` non-existent tag_ids
- [ ] TEST 4.26 — `refresh_accounts` happy path (post-fix)

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
- [ ] TEST 5.11 — `get_transactions` with account_id + date range combined
- [ ] TEST 5.12 — `get_transactions` with negative limit
- [ ] TEST 5.13 — `get_transactions` with negative offset
- [ ] TEST 5.14 — `get_transactions` with very large limit (10000)
- [ ] TEST 5.15 — `get_cashflow` with invalid date format
- [ ] TEST 5.16 — `get_cashflow` with future dates
- [ ] TEST 5.17 — `get_budgets` with invalid date format
- [ ] TEST 5.18 — `get_budgets` with future dates
- [ ] TEST 5.19 — `update_transaction` with invalid date format
- [ ] TEST 5.20 — `create_transaction` with very large amount

## Phase 6: Authentication
- [x] TEST 6.1 — `check_auth_status` PASS: "Authentication token found in secure keyring storage"
- [x] TEST 6.2 — `debug_session_loading` PASS: "Token found in keyring (length: 64)"
- [x] TEST 6.3 — `setup_authentication` PASS: returns instruction text

## Phase 7: Input Sanitization and Special Characters
- [ ] TEST 7.1 — Unicode in tag name
- [ ] TEST 7.2 — Unicode in merchant name (create_transaction)
- [ ] TEST 7.3 — Very long string in notes (update_transaction)
- [ ] TEST 7.4 — Very long tag name
- [ ] TEST 7.5 — HTML/script injection in merchant name
- [ ] TEST 7.6 — Special characters in tag name

## Phase 8: Auth Error Recovery
- [ ] TEST 8.1 — Expired token triggers re-auth flow (manual/observational)
- [ ] TEST 8.2 — `is_auth_error` correctly identifies 401/403 (unit test)

## Cleanup
- [x] Revert modified transactions (notes reverted to empty)
- [ ] Delete test tags "MCP-Test-Tag" and "Test Tag" via Monarch web UI
- [x] Remove test tags from transactions (removed via `set_transaction_tags` empty list)
- [ ] Delete test transaction (id: 235545705347956487, $1 "MCP Test Merchant", 2025-01-01) via Monarch web UI
- [ ] Revert modified transactions from Phase 4 new tests (amounts, dates, merchants, categories, hide_from_reports, needs_review)
- [ ] Delete test transactions from Tests 4.9-4.15, 5.20, 7.2 via Monarch web UI
- [ ] Delete test tags from Phase 7 (Unicode, long name, special chars) via Monarch web UI

---

## Bug Fixes (after test confirmation)
- [x] Fix Bug A — `create_transaction`: match library signature (merchant_name + category_id required, description removed, notes added)
- [x] Fix Bug B — `refresh_accounts`: fetch all account IDs via get_accounts() then pass to request_accounts_refresh()
- [x] Fix Bug C — `get_transaction_tags`: read `householdTransactionTags` key
- [x] Fix Bug D — `get_budgets`: return raw API response, accept start_date/end_date params
- [x] Fix Bug E — `get_transactions` account filter: pass `account_ids=[account_id]` (list)
- [x] Fix Bug F — `get_transactions` single date: validate both dates required with user-friendly error
- [x] Fix Bug G — `get_cashflow` single date: same validation as Bug F
- [x] Fix Bug H — `get_transactions` `is_pending`: read `pending` field
- [x] Fix Bug I — `get_transactions` `description`: removed nonexistent field
- [x] Fix Bug J — `create_transaction`: all required args passed directly, no conditional checks
- [x] Fix Bug K — Removed `MonarchConfig` class + cleaned up unused imports

## Post-fix Verification (MCP server restarted)
- [x] Bug A — `create_transaction` creates transaction successfully
- [x] Bug B — `refresh_accounts` returns `true`
- [x] Bug C — `get_transaction_tags` returns 9 tags (was `[]`)
- [x] Bug D — `get_budgets` returns full budget data with budgetData, categoryGroups, goalsV2 (was `[]`)
- [x] Bug E — `get_transactions(account_id=...)` returns filtered transactions for Chase checking
- [x] Bug F — `get_transactions(start_date=...)` returns `{"error": "Both start_date and end_date are required..."}`
- [x] Bug G — `get_cashflow(start_date=...)` returns `{"error": "Both start_date and end_date are required..."}`
- [x] Bug H — `is_pending` now shows `true` for pending transactions (was always `false`)
- [x] Bug I — `description` field removed from output
- [x] All 11 fixes verified working against live API

## Potential New Bugs (from gap analysis)
- [x] Fix Bug L — `get_budgets`: add `bool(start_date) != bool(end_date)` validation (same fix as Bugs F/G)
- [x] Verify Bug L fix after MCP server restart — returns `{"error": "Both start_date and end_date are required when filtering by date."}`

## Unit Tests (after all fixes)
- [ ] Design unit test architecture (mocking strategy, fixtures)
- [ ] Write unit tests for all tools
- [ ] Verify tests pass
