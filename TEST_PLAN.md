# Test Plan: Monarch Money MCP Server

## Context

This MCP server has no tests. Before writing unit tests, we execute a manual test plan against the live Monarch Money API to:
1. Discover bugs by testing real-world scenarios (not just confirming what the code does)
2. Fix all discovered issues
3. Then write unit tests to lock in correct behavior

Code review against the underlying `monarchmoney` library (v1.3.0, community fork) revealed **11 bugs**, including 4 critical ones where tools are completely broken.

## Bugs Discovered During Code Review

### CRITICAL — Tool completely broken on every call

| Bug | Tool | Root Cause | Server Line | Library Line |
|-----|------|-----------|-------------|-------------|
| **A** | `create_transaction` | Passes `description=` kwarg but library has no such param. Library requires `merchant_name` and `category_id` as mandatory positional args, but MCP treats them as optional. | server.py:401 | monarchmoney.py:1603-1612 |
| **B** | `refresh_accounts` | Calls `request_accounts_refresh()` with no args, but library requires `account_ids: List[str]` | server.py:487 | monarchmoney.py:671 |
| **C** | `get_transaction_tags` | Reads `tags.get("tags", [])` but API returns data under `householdTransactionTags` key | server.py:510 | monarchmoney.py:1951 |
| **D** | `get_budgets` | Reads `budgets.get("budgets", [])` but API returns under `budgetData` key with a completely different structure (monthly amounts by category, not flat budget list) | server.py:301 | monarchmoney.py:1206 |

### HIGH — Crashes under specific conditions

| Bug | Tool | Root Cause |
|-----|------|-----------|
| **E** | `get_transactions` with `account_id` | Passes `account_id=<str>` but library expects `account_ids=List[str]` (plural, list) |
| **F** | `get_transactions` with single date | Library requires both `start_date` AND `end_date` or neither |
| **G** | `get_cashflow` with single date | Same as F — library raises if only one date provided |

### MEDIUM — Incorrect data returned silently

| Bug | Tool | Root Cause |
|-----|------|-----------|
| **H** | `get_transactions` -> `is_pending` | Reads `txn.get("isPending")` but GraphQL field is `pending` — always returns `False` |
| **I** | `get_transactions` -> `description` | Reads `txn.get("description")` but no such field in GraphQL response — always returns `null` |
| **J** | `create_transaction` vs `update_transaction` | Create uses `if category_id:` (falsy check) while update uses `if category_id is not None:` (None check) — inconsistent handling of empty strings |

### LOW

| Bug | Notes |
|-----|-------|
| **K** | `MonarchConfig` class defined (server.py:67-74) but never used — dead code |

---

## Test Execution Plan

### Phase 1: Confirm Critical Crashes

Run these first to confirm the 4 completely broken tools.

**TEST 1.1 — `create_transaction` always fails (Bug A)**
```
create_transaction(
  account_id="<any valid account id>",
  amount=-25.99,
  description="Test purchase",
  date="2025-06-15",
  merchant_name="Test Merchant",
  category_id="<any valid category id>"
)
```
- Expected: Error containing "unexpected keyword argument 'description'"
- Confirms: Bug A

**TEST 1.2 — `refresh_accounts` always fails (Bug B)**
```
refresh_accounts()
```
- Expected: Error containing "missing 1 required positional argument: 'account_ids'"
- Confirms: Bug B

**TEST 1.3 — `get_transaction_tags` returns empty (Bug C)**
```
get_transaction_tags()
```
- Expected: Returns `[]` even if tags exist in Monarch web UI
- Confirm by: Checking Monarch web UI -> Settings -> Tags

**TEST 1.4 — `get_budgets` returns empty (Bug D)**
```
get_budgets()
```
- Expected: Returns `[]` even if budgets are configured in Monarch web UI
- Confirm by: Checking Monarch web UI -> Budget page

---

### Phase 2: Verify Working Read Operations

**TEST 2.1 — `get_accounts` happy path**
```
get_accounts()
```
- Verify: Valid JSON array returned, each with `id`, `name`, `type`, `balance`, `institution`, `is_active`
- Cross-check: Count matches Monarch web UI account count
- Cross-check: Balances match web UI (snapshot them at the same time)
- Cross-check: Account names match
- Check: Any account with `type: null` or `institution: null` — is this correct?
- Check: `is_active` is correct for any deactivated accounts

**TEST 2.2 — `get_transactions` happy path (no filters)**
```
get_transactions(limit=10)
```
- Verify: Returns 10 transactions, each with required fields
- Cross-check: Compare the top 5 transactions against Monarch web UI -> Transactions page
- Check specifically: `amount`, `date`, `category`, `merchant`, `account` fields match web UI
- Check: `description` field — expect always `null` (Bug I)
- Check: `is_pending` — if any transaction is pending in web UI but shows `false` here (Bug H)

**TEST 2.3 — `get_transactions` with date range**
```
get_transactions(limit=100, start_date="2025-01-01", end_date="2025-01-31")
```
- Verify: All returned transactions have dates within Jan 2025
- Cross-check: Count against Monarch web UI filtered to Jan 2025

**TEST 2.4 — `get_cashflow` happy path**
```
get_cashflow(start_date="2025-01-01", end_date="2025-01-31")
```
- Verify: Returns JSON with `byCategory`, `byCategoryGroup`, `byMerchant`, `summary` keys
- Cross-check: `summary` -> `sumIncome` and `sumExpense` match Monarch web UI cashflow page for Jan 2025
- Note: This tool returns raw API response (no reformatting), unlike other tools

**TEST 2.5 — `get_account_holdings` happy path**
- Prerequisite: Find a brokerage/investment account from TEST 2.1
```
get_account_holdings(account_id="<brokerage_account_id>")
```
- Verify: Returns holdings data with tickers/values
- Cross-check: A few ticker symbols and values against web UI

**TEST 2.6 — `get_budgets` happy path (both dates)**
```
get_budgets(start_date="2025-01-01", end_date="2025-01-31")
```
- Verify: Returns JSON with `budgetData`, `categoryGroups`, `goalsV2` keys
- Cross-check: At least one category has a non-zero `plannedCashFlowAmount` matching Monarch web UI budget page for Jan 2025
- Note: This returns raw API response (no reformatting)

**TEST 2.7 — `get_budgets` happy path (no dates — defaults)**
```
get_budgets()
```
- Verify: Returns same structure as 2.6 with library-default date range
- Verify: Response is non-empty (not `{}` or `null`)

**TEST 2.8 — `get_cashflow` happy path (no dates — defaults)**
```
get_cashflow()
```
- Verify: Returns JSON with `byCategory`, `byCategoryGroup`, `byMerchant`, `summary` keys
- Verify: Response covers the current month by default

---

### Phase 3: Confirm Conditional Failures

**TEST 3.1 — `get_transactions` with `account_id` filter (Bug E)**
- Use an account ID from TEST 2.1
```
get_transactions(limit=10, account_id="<valid_account_id>")
```
- Expected: Error — `account_id` is wrong kwarg name (library expects `account_ids` as a list)
- Confirms: Bug E

**TEST 3.2 — `get_transactions` with only `start_date` (Bug F)**
```
get_transactions(limit=10, start_date="2025-01-01")
```
- Expected: Error "You must specify both a startDate and endDate"
- Confirms: Bug F

**TEST 3.3 — `get_transactions` with only `end_date` (Bug F variant)**
```
get_transactions(limit=10, end_date="2025-12-31")
```
- Expected: Same error as 3.2

**TEST 3.4 — `get_cashflow` with only `start_date` (Bug G)**
```
get_cashflow(start_date="2025-01-01")
```
- Expected: Error "You must specify both a startDate and endDate"
- Confirms: Bug G

**TEST 3.5 — `get_budgets` with only `start_date` (potential Bug L)**
```
get_budgets(start_date="2025-01-01")
```
- Expected: Either a graceful error or the library handles it — but likely crashes the same way as Bugs F/G
- Note: The current code has NO `bool(start_date) != bool(end_date)` validation unlike `get_transactions` and `get_cashflow`
- If crash: This is a new bug (same class as F/G, fix was never applied to `get_budgets`)

**TEST 3.6 — `get_budgets` with only `end_date` (potential Bug L variant)**
```
get_budgets(end_date="2025-01-31")
```
- Expected: Same behavior as 3.5

**TEST 3.7 — `get_cashflow` with only `end_date` (Bug G variant)**
```
get_cashflow(end_date="2025-01-31")
```
- Expected: Error "Both start_date and end_date are required when filtering by date."
- Verify: The validation catches end_date-only the same as start_date-only

---

### Phase 4: Verify Write Operations

**TEST 4.1 — `update_transaction` — update notes (happy path)**
- Get a transaction ID from `get_transactions(limit=1)`
- Note original notes value
```
update_transaction(transaction_id="<txn_id>", notes="MCP test - will revert")
```
- Verify: Response includes updated notes
- Cross-check: Verify in web UI
- Cleanup: Revert with `update_transaction(transaction_id="<txn_id>", notes="<original_notes>")`

**TEST 4.2 — `update_transaction` — no-op (only transaction_id)**
```
update_transaction(transaction_id="<valid_txn_id>")
```
- Expected: Succeeds with no changes (documented library behavior)

**TEST 4.3 — `update_transaction` — invalid transaction_id**
```
update_transaction(transaction_id="nonexistent-id-12345", notes="should fail")
```
- Expected: Graceful error message

**TEST 4.4 — `create_transaction_tag` — happy path**
```
create_transaction_tag(name="MCP-Test-Tag", color="#FF5733")
```
- Expected: Returns created tag with `id`, `name`, `color`
- Cross-check: Verify tag appears in Monarch web UI -> Settings -> Tags
- Save the returned tag ID for TEST 4.7

**TEST 4.5 — `create_transaction_tag` — validation: bad color**
```
create_transaction_tag(name="Bad", color="red")
```
- Expected: `{"error": "Invalid color format..."}`

**TEST 4.6 — `create_transaction_tag` — validation: empty name**
```
create_transaction_tag(name="", color="#FF5733")
```
- Expected: `{"error": "Tag name cannot be empty"}`

**TEST 4.7 — `set_transaction_tags` — apply tag to transaction**
- Use tag ID from TEST 4.4 and a transaction ID
```
set_transaction_tags(transaction_id="<txn_id>", tag_ids=["<tag_id>"])
```
- Expected: Success
- Cross-check: Verify tag appears on transaction in web UI

**TEST 4.8 — `set_transaction_tags` — remove all tags**
```
set_transaction_tags(transaction_id="<txn_id>", tag_ids=[])
```
- Expected: All tags removed from the transaction
- Cross-check: Verify in web UI

**TEST 4.9 — `create_transaction` — happy path (post-fix)**
- Prerequisite: Get a valid account_id from TEST 2.1 and a category_id from a recent transaction
```
create_transaction(
  account_id="<valid_account_id>",
  amount=-15.50,
  merchant_name="MCP Test Merchant",
  category_id="<valid_category_id>",
  date="2025-01-01",
  notes="Test transaction - will delete"
)
```
- Verify: Returns created transaction with all fields
- Cross-check: Transaction appears in Monarch web UI
- Cleanup: Delete via Monarch web UI

**TEST 4.10 — `create_transaction` — positive amount (income)**
```
create_transaction(
  account_id="<valid_account_id>",
  amount=100.00,
  merchant_name="MCP Test Income",
  category_id="<valid_category_id>",
  date="2025-01-01"
)
```
- Verify: Transaction created with positive amount
- Cleanup: Delete via Monarch web UI

**TEST 4.11 — `create_transaction` — without optional `notes`**
```
create_transaction(
  account_id="<valid_account_id>",
  amount=-5.00,
  merchant_name="MCP No Notes Test",
  category_id="<valid_category_id>",
  date="2025-01-01"
)
```
- Verify: Transaction created successfully; notes field is empty string (code maps `None` to `""`)
- Cleanup: Delete via Monarch web UI

**TEST 4.12 — `create_transaction` — invalid account_id**
```
create_transaction(
  account_id="nonexistent-account-99999",
  amount=-10.00,
  merchant_name="Should Fail",
  category_id="<valid_category_id>",
  date="2025-01-01"
)
```
- Expected: Graceful error (GraphQL error propagated as string, not server crash)

**TEST 4.13 — `create_transaction` — invalid category_id**
```
create_transaction(
  account_id="<valid_account_id>",
  amount=-10.00,
  merchant_name="Should Fail",
  category_id="nonexistent-category-99999",
  date="2025-01-01"
)
```
- Expected: Graceful error or API creates with no category — observe behavior

**TEST 4.14 — `create_transaction` — invalid date format**
```
create_transaction(
  account_id="<valid_account_id>",
  amount=-10.00,
  merchant_name="Bad Date",
  category_id="<valid_category_id>",
  date="not-a-date"
)
```
- Expected: Graceful error, not server crash

**TEST 4.15 — `create_transaction` — amount=0**
```
create_transaction(
  account_id="<valid_account_id>",
  amount=0,
  merchant_name="Zero Amount Test",
  category_id="<valid_category_id>",
  date="2025-01-01"
)
```
- Expected: Either succeeds (zero-dollar transaction) or graceful error
- Cleanup: Delete via web UI if created

**TEST 4.16 — `update_transaction` — update amount**
- Get a transaction ID; note original amount
```
update_transaction(transaction_id="<txn_id>", amount=-99.99)
```
- Verify: Response reflects the updated amount
- Cleanup: Revert to original amount

**TEST 4.17 — `update_transaction` — update merchant_name**
- Note original merchant
```
update_transaction(transaction_id="<txn_id>", merchant_name="MCP Updated Merchant")
```
- Verify: Response reflects updated merchant
- Cleanup: Revert to original merchant name

**TEST 4.18 — `update_transaction` — update date**
- Note original date
```
update_transaction(transaction_id="<txn_id>", date="2025-06-15")
```
- Verify: Response reflects updated date
- Cleanup: Revert to original date

**TEST 4.19 — `update_transaction` — toggle hide_from_reports**
```
update_transaction(transaction_id="<txn_id>", hide_from_reports=true)
```
- Verify: Response shows transaction hidden
- Cross-check: Verify in web UI if possible
- Cleanup: `update_transaction(transaction_id="<txn_id>", hide_from_reports=false)`

**TEST 4.20 — `update_transaction` — toggle needs_review**
```
update_transaction(transaction_id="<txn_id>", needs_review=false)
```
- Verify: Response reflects the change
- Cleanup: Revert if needed

**TEST 4.21 — `update_transaction` — update multiple fields at once**
```
update_transaction(
  transaction_id="<txn_id>",
  merchant_name="Multi-Update Test",
  notes="Multi-field update",
  needs_review=true
)
```
- Verify: All three fields updated in response
- Cleanup: Revert all fields

**TEST 4.22 — `update_transaction` — update category_id**
- Get a valid category_id from any transaction
```
update_transaction(transaction_id="<txn_id>", category_id="<different_category_id>")
```
- Verify: Category changed in response
- Cleanup: Revert to original category

**TEST 4.23 — `set_transaction_tags` — apply multiple tags**
- Create a second test tag if needed, or use two existing tag IDs
```
set_transaction_tags(transaction_id="<txn_id>", tag_ids=["<tag_id_1>", "<tag_id_2>"])
```
- Verify: Both tags appear on the transaction
- Cleanup: Remove with `set_transaction_tags(transaction_id="<txn_id>", tag_ids=[])`

**TEST 4.24 — `set_transaction_tags` — invalid transaction_id**
```
set_transaction_tags(transaction_id="nonexistent-id-99999", tag_ids=["<valid_tag_id>"])
```
- Expected: Graceful error, not server crash

**TEST 4.25 — `set_transaction_tags` — non-existent tag_ids**
```
set_transaction_tags(transaction_id="<valid_txn_id>", tag_ids=["fake-tag-99999"])
```
- Expected: Graceful error or API ignores invalid tags — observe behavior

**TEST 4.26 — `refresh_accounts` — happy path (post-fix)**
```
refresh_accounts()
```
- Verify: Returns a response (expected `true` or success indicator)
- Note: This triggers actual refreshes with financial institutions; may take time

---

### Phase 5: Edge Cases and Boundary Testing

**TEST 5.1 — Pagination: page 1 vs page 2**
```
get_transactions(limit=5, offset=0)
get_transactions(limit=5, offset=5)
```
- Verify: No overlapping transaction IDs between pages
- Verify: Page 2 dates are same or older than page 1

**TEST 5.2 — Pagination: very large offset**
```
get_transactions(limit=10, offset=999999)
```
- Expected: Empty array `[]`, no crash

**TEST 5.3 — Limit boundary: limit=0**
```
get_transactions(limit=0)
```
- Expected: Either empty array or API-defined behavior, no crash

**TEST 5.4 — Invalid date format**
```
get_transactions(limit=10, start_date="not-a-date", end_date="also-not")
```
- Expected: Error caught and returned as string, not server crash

**TEST 5.5 — Future dates (empty result)**
```
get_transactions(limit=10, start_date="2030-01-01", end_date="2030-12-31")
```
- Expected: Empty array `[]`

**TEST 5.6 — Holdings for non-investment account**
- Use a checking account ID from TEST 2.1
```
get_account_holdings(account_id="<checking_account_id>")
```
- Expected: Empty result or graceful error

**TEST 5.7 — Holdings for invalid account_id**
```
get_account_holdings(account_id="nonexistent-99999")
```
- Expected: Graceful error message

**TEST 5.8 — Tag validation: 3-digit hex**
```
create_transaction_tag(name="Short", color="#F00")
```
- Expected: Validation error (regex requires 6 hex digits)

**TEST 5.9 — Tag validation: whitespace-only name**
```
create_transaction_tag(name="   ", color="#FF5733")
```
- Expected: `{"error": "Tag name cannot be empty"}`

**TEST 5.10 — Duplicate tag name**
```
create_transaction_tag(name="MCP-Test-Tag", color="#00FF00")
```
- Observe: Does API allow duplicate names?

**TEST 5.11 — `get_transactions` with `account_id` + date range combined**
- Use a valid account_id from TEST 2.1
```
get_transactions(limit=50, account_id="<valid_account_id>", start_date="2025-01-01", end_date="2025-01-31")
```
- Verify: All returned transactions belong to the specified account AND fall within Jan 2025
- Verify: No crash when combining both filters

**TEST 5.12 — `get_transactions` with negative limit**
```
get_transactions(limit=-1)
```
- Expected: Graceful error or empty result, not server crash

**TEST 5.13 — `get_transactions` with negative offset**
```
get_transactions(limit=10, offset=-1)
```
- Expected: Graceful error or treated as 0, not server crash

**TEST 5.14 — `get_transactions` with very large limit**
```
get_transactions(limit=10000)
```
- Expected: Returns transactions (possibly capped by API) without timeout or crash
- Note: May be slow; observe response time

**TEST 5.15 — `get_cashflow` with invalid date format**
```
get_cashflow(start_date="not-a-date", end_date="also-not")
```
- Expected: Error caught and returned as string, not server crash

**TEST 5.16 — `get_cashflow` with future dates (empty result)**
```
get_cashflow(start_date="2030-01-01", end_date="2030-12-31")
```
- Expected: Returns structure with zero sums, not crash

**TEST 5.17 — `get_budgets` with invalid date format**
```
get_budgets(start_date="not-a-date", end_date="also-not")
```
- Expected: Error caught and returned as string, not server crash

**TEST 5.18 — `get_budgets` with future dates**
```
get_budgets(start_date="2030-01-01", end_date="2030-12-31")
```
- Expected: Returns structure with zero/empty budgets, not crash

**TEST 5.19 — `update_transaction` with invalid date format**
```
update_transaction(transaction_id="<valid_txn_id>", date="not-a-date")
```
- Expected: Graceful error, not server crash

**TEST 5.20 — `create_transaction` with very large amount**
```
create_transaction(
  account_id="<valid_account_id>",
  amount=-999999999.99,
  merchant_name="Big Amount Test",
  category_id="<valid_category_id>",
  date="2025-01-01"
)
```
- Expected: Either succeeds or graceful error from API
- Cleanup: Delete via web UI if created

---

### Phase 6: Authentication

**TEST 6.1 — `check_auth_status`**
```
check_auth_status()
```
- Expected: "Authentication token found in secure keyring storage"

**TEST 6.2 — `debug_session_loading`**
```
debug_session_loading()
```
- Expected: "Token found in keyring (length: N)" with reasonable N

**TEST 6.3 — `setup_authentication`**
```
setup_authentication()
```
- Expected: Multi-line instruction string (pure text, no API call)

---

### Phase 7: Input Sanitization and Special Characters

**TEST 7.1 — Unicode in tag name**
```
create_transaction_tag(name="テスト-Tag-🏷️", color="#AA00FF")
```
- Expected: Either succeeds (API accepts Unicode) or graceful error
- Cleanup: Delete via web UI if created

**TEST 7.2 — Unicode in merchant name (create_transaction)**
```
create_transaction(
  account_id="<valid_account_id>",
  amount=-10.00,
  merchant_name="カフェ Tokyo ☕",
  category_id="<valid_category_id>",
  date="2025-01-01"
)
```
- Expected: Succeeds or graceful error
- Cleanup: Delete via web UI if created

**TEST 7.3 — Very long string in notes**
```
update_transaction(transaction_id="<valid_txn_id>", notes="<1000+ character string>")
```
- Expected: Succeeds (notes may be truncated) or graceful error
- Cleanup: Revert notes to original value

**TEST 7.4 — Very long tag name**
```
create_transaction_tag(name="<200+ character string>", color="#00AAFF")
```
- Expected: Succeeds or API rejects with a length error — not a server crash
- Cleanup: Delete via web UI if created

**TEST 7.5 — HTML/script injection in merchant name**
```
update_transaction(transaction_id="<valid_txn_id>", merchant_name="<script>alert(1)</script>")
```
- Expected: Stored as literal text (Monarch API is not a browser), no crash
- Verify: Value stored literally, not interpreted
- Cleanup: Revert merchant name

**TEST 7.6 — Special characters in tag name**
```
create_transaction_tag(name="Test & 'Quotes' \"Double\"", color="#FFAA00")
```
- Expected: Succeeds or graceful error (GraphQL serialization handles escaping)
- Cleanup: Delete via web UI if created

---

### Phase 8: Auth Error Recovery (Observational)

These tests verify the auto-re-auth path in `run_async()` (server.py:29-59). They are
difficult to trigger without deliberately invalidating the token, so they may need to be
tested via unit tests with mocking rather than live API calls.

**TEST 8.1 — Expired token triggers re-auth flow**
- Prerequisite: Manually corrupt the keyring token (save a fake token via `secure_session.save_token("invalid_token_abc123")`)
```
get_accounts()
```
- Expected: `run_async` detects `is_auth_error`, deletes the stale token, triggers `trigger_auth_flow()`, and raises a RuntimeError with message "Your session has expired..."
- Verify: A browser window opens for re-authentication
- Cleanup: Re-authenticate via browser

**TEST 8.2 — `is_auth_error` correctly identifies 401/403**
- This is best tested via unit test
- Verify: `TransportServerError` with code=401 returns `True`
- Verify: `TransportServerError` with code=403 returns `True`
- Verify: `TransportServerError` with code=500 returns `False`
- Verify: `LoginFailedException` returns `True`
- Verify: Generic `Exception` returns `False`

---

### Cleanup After Testing

1. Revert any modified transactions (notes, amounts, dates, merchant names, hide_from_reports, needs_review, categories)
2. Delete test tags ("MCP-Test-Tag", Unicode tags, long-name tags, special-char tags, and any duplicates) via Monarch web UI
3. Remove any test tags from transactions
4. Delete test transactions (any created by Tests 4.9-4.15, 5.20, 7.2) via Monarch web UI

---

## Summary of Expected Results

### Pre-fix status (original bugs)

| Tool | Status | Bugs |
|------|--------|------|
| `setup_authentication` | Working | -- |
| `check_auth_status` | Working | -- |
| `debug_session_loading` | Working | -- |
| `get_accounts` | Working | Minor: displayName fallback |
| `get_transactions` (no filter) | Partially working | H (is_pending always false), I (description always null) |
| `get_transactions` (account filter) | Broken | E (wrong param name) |
| `get_transactions` (single date) | Broken | F (must provide both dates) |
| `get_budgets` | Broken | D (wrong response key + wrong data model) |
| `get_cashflow` (both dates) | Working | -- |
| `get_cashflow` (single date) | Broken | G (must provide both dates) |
| `get_account_holdings` | Working | -- |
| `create_transaction` | Broken | A (wrong params, missing required args) |
| `update_transaction` | Working | J (minor inconsistency) |
| `refresh_accounts` | Broken | B (missing required arg) |
| `get_transaction_tags` | Broken | C (wrong response key) |
| `create_transaction_tag` | Working | -- |
| `set_transaction_tags` | Working | -- |

**5 tools completely broken, 1 partially broken, 8 working**

### Test coverage by tool (post-fix)

| Tool | Phase 1-3 (bugs) | Phase 2/4 (happy path) | Phase 5 (edge cases) | Phase 7 (input) | Total tests |
|------|:-:|:-:|:-:|:-:|:-:|
| `setup_authentication` | -- | 6.3 | -- | -- | 1 |
| `check_auth_status` | -- | 6.1 | -- | -- | 1 |
| `debug_session_loading` | -- | 6.2 | -- | -- | 1 |
| `get_accounts` | -- | 2.1 | -- | -- | 1 |
| `get_transactions` | 3.1-3.3 | 2.2, 2.3 | 5.1-5.5, 5.11-5.14 | -- | 14 |
| `get_budgets` | 1.4, 3.5-3.6 | 2.6, 2.7 | 5.17-5.18 | -- | 6 |
| `get_cashflow` | 3.4, 3.7 | 2.4, 2.8 | 5.15-5.16 | -- | 6 |
| `get_account_holdings` | -- | 2.5 | 5.6-5.7 | -- | 3 |
| `create_transaction` | 1.1 | 4.9-4.11 | 4.12-4.15, 5.20 | 7.2 | 9 |
| `update_transaction` | -- | 4.1-4.2, 4.16-4.22 | 4.3, 5.19 | 7.3, 7.5 | 12 |
| `refresh_accounts` | 1.2 | 4.26 | -- | -- | 2 |
| `get_transaction_tags` | 1.3 | -- | -- | -- | 1 |
| `create_transaction_tag` | -- | 4.4 | 4.5-4.6, 5.8-5.10 | 7.1, 7.4, 7.6 | 8 |
| `set_transaction_tags` | -- | 4.7-4.8, 4.23 | 4.24-4.25 | -- | 5 |
| Auth error recovery | -- | -- | 8.1-8.2 | -- | 2 |
| **Total** | | | | | **72** |

### Potential new bug found during gap analysis

| Bug | Tool | Root Cause |
|-----|------|-----------|
| **L** (potential) | `get_budgets` with single date | No `bool(start_date) != bool(end_date)` validation — same class of bug as F/G, fix was never applied to `get_budgets`. Tests 3.5-3.6 will confirm. |
