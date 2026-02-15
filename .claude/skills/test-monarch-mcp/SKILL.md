---
name: test-monarch-mcp
description: Systematically test all 39 Monarch Money MCP tools — happy paths, edge cases, and error handling. Account-agnostic (discovers IDs at runtime) and self-cleaning (deletes everything it creates).
user_invocable: true
---

# Test Monarch MCP Skill

You are executing a comprehensive test suite for the Monarch Money MCP server.
Run all 127 tests across 12 phases, track results, and clean up after yourself.

---

## Write Mode Requirement

This test suite creates, updates, and deletes data. The server must be running
with **write tools enabled** (`--enable-write`). When running against the MCP
tools directly (as this skill does), write mode is required — otherwise the 13
write tools will be hidden and the mutation phases will fail.

---

## State File Management

The state file is `mcp-test-state.json` in the project root (`C:\dev\monarch-mcp\monarch-mcp-server\mcp-test-state.json`).

### On Invocation — Check for Existing State

1. Try to read `mcp-test-state.json`.
2. **Not found** → Start a fresh run from Phase 0.
3. **Found with `status: "in_progress"`** → Ask the user:
   - "Resume from Phase {last_completed_phase + 1}?"
   - "Clean up and start fresh?"
   - "Clean up only?"
4. **Found with `status: "cleanup_needed"`** → Run cleanup using stored IDs, then delete state file.
5. **Found with `status: "completed"`** → Show previous results summary, ask: "Run again?" If yes, delete state file and start fresh.

### State File Structure

```json
{
  "status": "in_progress | completed | cleanup_needed",
  "started_at": "<ISO timestamp>",
  "last_updated": "<ISO timestamp>",
  "last_completed_phase": 0,
  "discovery": {
    "checking_account_id": "",
    "investment_account_id": "",
    "test_transaction_id": "",
    "valid_category_id": "",
    "original_values": {
      "merchant": "",
      "notes": "",
      "amount": 0,
      "date": "",
      "category_id": "",
      "hide_from_reports": false,
      "needs_review": false
    }
  },
  "created_resources": {
    "transactions": [],
    "tags": [],
    "categories": [],
    "accounts": []
  },
  "results": {},
  "summary": {
    "total": 127,
    "passed": 0,
    "failed": 0,
    "skipped": 0
  }
}
```

### Update Cadence

- **Write** the state file after Phase 0 (discovery IDs are now logged).
- **Update** after each completed phase (bump `last_completed_phase`, add test results).
- **Update `created_resources` immediately** after every `create_transaction` or `create_transaction_tag` call — before running the next test.
- Set `status: "completed"` after cleanup succeeds, then **delete** the state file.

---

## Error Handling Rules

- **Phase 0 failure = HALT.** If discovery fails, do not proceed. Write state file with `status: "cleanup_needed"` and stop.
- **All other phases: log and continue.** If a test fails, record `FAIL` with details and move to the next test.
- **Cleanup always runs.** Even if a phase throws an unexpected error, jump to cleanup.
- **Test data naming:** All test merchants are prefixed with `MCP-Test-` and all test tags are prefixed with `MCP-Test-` for easy identification.

---

## Pre-flight Warning

Before starting any test work (including Phase 0), display this warning and **STOP and wait for explicit user approval**:

---

**WARNING: This test suite operates on your live Monarch Money account.**

- It **creates and deletes** transactions, tags, categories, and accounts.
- It **temporarily modifies** an existing transaction (then reverts it).
- The test is designed to clean up everything it creates, but **if something goes wrong** (network error, timeout, context limit), **cleanup may be incomplete** and unwanted changes could remain in your account.
- All test-created data is prefixed with `MCP-Test-` for easy manual identification.
- If the session is interrupted, you can **resume where you left off** by invoking this skill again — it will detect the saved progress and offer to continue.

**Do you want to continue?**

---

Do NOT proceed until the user explicitly confirms. If the user declines, stop immediately.

This warning applies to **fresh runs only**. When resuming an in-progress run or performing cleanup-only, skip this warning (the user already accepted the risk).

---

## Phase 0 — Discovery

This phase runs first. No reference file — execute inline.

1. Call `get_accounts()`.
   - Extract `checking_account_id`: first account whose `type` field contains "checking" (case-insensitive). Fallback: the first account in the list.
   - Extract `investment_account_id`: first account whose `type` field contains "investment" or "brokerage" (case-insensitive). May be null if none found.

2. Call `get_transactions(limit=5)`.
   - Extract `test_transaction_id`: the first transaction's ID.
   - Extract `valid_category_id`: the first transaction's category ID.
   - Record **original values** for the test transaction: `merchant` (or `merchant_name`), `notes`, `amount`, `date`, `category_id`, `hide_from_reports`, `needs_review`.

3. Initialize `created_resources = { transactions: [], tags: [] }`.

4. Write the state file with `status: "in_progress"`, `last_completed_phase: 0`.

5. Print discovery results:
   ```
   === Phase 0: Discovery ===
   Checking account:    {id} ({name})
   Investment account:  {id} ({name}) or "None found"
   Test transaction:    {id} ({merchant}, ${amount})
   Valid category:      {id} ({name})
   ```

If any required value (`checking_account_id`, `test_transaction_id`, `valid_category_id`) is missing, HALT.

---

## Phase 1 — Auth Tools (3 tests)

Load and follow: `references/auth-tools.md`

After completing all tests, update state file: `last_completed_phase: 1`, add results.

---

## Phase 2 — Accounts & Holdings (5 tests)

Load and follow: `references/accounts-and-holdings.md`

Uses `checking_account_id` and `investment_account_id` from discovery.

After completing all tests, update state file: `last_completed_phase: 2`, add results.

---

## Phase 3 — Transaction Reads (14 tests)

Load and follow: `references/transactions-read.md`

Uses `checking_account_id` from discovery.

After completing all tests, update state file: `last_completed_phase: 3`, add results.

---

## Phase 4 — Budgets, Cashflow & Budget Amounts (15 tests)

Load and follow: `references/budgets-and-cashflow.md`

After completing all tests, update state file: `last_completed_phase: 4`, add results.

---

## Phase 5 — Tag CRUD (13 tests)

Load and follow: `references/tag-crud.md`

**Important:** Track every created tag ID in `created_resources.tags` immediately after creation.

After completing all tests, update state file: `last_completed_phase: 5`, add results.

---

## Phase 6 — Transaction CRUD (25 tests)

Load and follow: `references/transaction-crud.md`

Uses `checking_account_id`, `valid_category_id`, and `test_transaction_id` from discovery.

**Important:** Track every created transaction ID in `created_resources.transactions` immediately after creation.

After completing all tests, update state file: `last_completed_phase: 6`, add results.

---

## Phase 7 — Transaction Tagging (5 tests)

Load and follow: `references/transaction-tagging.md`

This phase creates its own temporary tag(s) for testing. Track them in `created_resources.tags`.

After completing all tests, update state file: `last_completed_phase: 7`, add results.

---

## Phase 8 — Categories (10 tests)

Load and follow: `references/categories.md`

Tests `get_transaction_categories`, `get_transaction_category_groups`, `create_transaction_category`, and `delete_transaction_category`.

**Important:** Track every created category ID in `created_resources.categories` immediately after creation.

After completing all tests, update state file: `last_completed_phase: 8`, add results.

---

## Phase 9 — Transaction Details & Splits (8 tests)

Load and follow: `references/transaction-details-and-splits.md`

Tests `get_transaction_details`, `get_transaction_splits`, and `update_transaction_splits`.

After completing all tests, update state file: `last_completed_phase: 9`, add results.

---

## Phase 10 — Read-Only Tools (9 tests)

Load and follow: `references/read-only-tools.md`

Tests `get_transactions_summary`, `get_subscription_details`, `get_institutions`, `get_cashflow_summary`, and `get_recurring_transactions`.

After completing all tests, update state file: `last_completed_phase: 10`, add results.

---

## Phase 11 — Account Management (10 tests)

Load and follow: `references/account-management.md`

Tests `create_manual_account`, `update_account`, `delete_account`, `get_account_type_options`, `get_account_history`, `get_recent_account_balances`, `get_account_snapshots_by_type`, `get_aggregate_snapshots`.

**Important:** Track every created account ID in `created_resources.accounts` immediately after creation.

After completing all tests, update state file: `last_completed_phase: 11`, add results.

---

## Phase 12 — Analytics Tools (5 tests)

Load and follow: `references/analytics-tools.md`

Tests `get_credit_history`, advanced transaction search filters.

After completing all tests, update state file: `last_completed_phase: 12`, add results.

---

## Cleanup Phase

**This phase ALWAYS runs**, even if earlier phases failed or were skipped.

### Step 1: Revert Test Transaction Mutations

Using `test_transaction_id` and `original_values` from state file:

```
update_transaction(
  transaction_id = {test_transaction_id},
  merchant_name  = {original_values.merchant},
  notes          = {original_values.notes},
  amount         = {original_values.amount},
  date           = {original_values.date},
  category_id    = {original_values.category_id},
  hide_from_reports = false,
  needs_review      = false
)
```

### Step 2: Remove Tags from Test Transaction

```
set_transaction_tags(
  transaction_id = {test_transaction_id},
  tag_ids        = []
)
```

### Step 3: Delete Created Transactions

For each ID in `created_resources.transactions`:
```
delete_transaction(transaction_id = {id})
```
Log success/failure for each. Continue on failure.

### Step 4: Delete Created Tags

For each ID in `created_resources.tags`:
```
delete_transaction_tag(tag_id = {id})
```
Log success/failure for each. Continue on failure.

### Step 4b: Delete Created Categories

For each ID in `created_resources.categories`:
```
delete_transaction_category(category_id = {id})
```
Log success/failure for each. Continue on failure.

### Step 4c: Delete Created Accounts

For each ID in `created_resources.accounts`:
```
delete_account(account_id = {id})
```
Log success/failure for each. Continue on failure.

### Step 5: Verify Tag Cleanup

Call `get_transaction_tags()`. Confirm none of the returned tags have names starting with `MCP-Test-`. If any remain, attempt to delete them and warn the user.

### Step 6: Finalize

Set `status: "completed"` in state file, then delete `mcp-test-state.json`.

---

## Reporting

After cleanup, print a final summary:

```
╔══════════════════════════════════════════╗
║       MCP Tool Test Results Summary      ║
╠══════════════════════════════════════════╣
║ Phase 1 — Auth Tools:        3/3  PASS   ║
║ Phase 2 — Accounts:          5/5  PASS   ║
║ Phase 3 — Transaction Reads: 14/14 PASS  ║
║ Phase 4 — Budgets/Cashflow:  12/12 PASS  ║
║ Phase 5 — Tag CRUD:          13/13 PASS  ║
║ Phase 6 — Transaction CRUD:  25/25 PASS  ║
║ Phase 7 — Tagging:           5/5  PASS   ║
╠══════════════════════════════════════════╣
║ TOTAL: 77 passed, 0 failed, 0 skipped   ║
╚══════════════════════════════════════════╝
```

If any tests failed, list each failure with:
- Test number and name
- Expected result
- Actual result
- Tool call parameters used

---

## Recording Test Results

For each test:

1. **Before calling the tool**, print: `[{test_number}] {tool_name} — {scenario}...`
2. **Call the tool** with the specified parameters.
3. **Evaluate** the result against the expected outcome listed in the reference file.
4. **Record** the result:
   - `PASS`: Result matched expectations. Record brief detail.
   - `FAIL`: Result did not match. Record expected vs. actual.
   - `SKIP`: Test could not run (e.g., no investment account for test 2.2). Record reason.
5. **Print** the result: `  → PASS` or `  → FAIL: {reason}` or `  → SKIP: {reason}`
6. **Update** the state file results and summary counts.

---

## Placeholder Reference

Throughout reference files, these placeholders map to discovery values:

| Placeholder | Source |
|---|---|
| `{checking_account_id}` | `discovery.checking_account_id` |
| `{investment_account_id}` | `discovery.investment_account_id` |
| `{test_transaction_id}` | `discovery.test_transaction_id` |
| `{valid_category_id}` | `discovery.valid_category_id` |
| `{created_tag_id}` | ID returned from the most recent `create_transaction_tag` call |
| `{created_txn_id}` | ID returned from the most recent `create_transaction` call |
