# Phase 2 — Accounts & Holdings (5 tests)

---

## Test 2.1 — get_accounts: Happy Path

**Tool call:**
```
get_accounts()
```

**Expected:** A non-empty list of accounts. Each account should have at least: `id`, `displayName` (or `name`), `type` (or `subtype`), and a balance-related field.

**Validation:**
- Response contains at least one account.
- Each account has an `id` field.
- Each account has a name field (`displayName` or `name`).
- Each account has a type or subtype field.

**Cleanup:** None.

---

## Test 2.2 — get_account_holdings: Investment Account

**Condition:** Only run if `{investment_account_id}` was discovered. If not, SKIP with reason "No investment account found."

**Tool call:**
```
get_account_holdings(account_id = "{investment_account_id}")
```

**Expected:** A dict or list containing holdings data. May be empty if the account has no holdings, but should not crash.

**Validation:** Response is a dict or list (not an error string). No exception or crash.

**Cleanup:** None.

---

## Test 2.3 — get_account_holdings: Non-Investment Account

**Tool call:**
```
get_account_holdings(account_id = "{checking_account_id}")
```

**Expected:** Either an empty list/dict or a graceful error message. Should not crash.

**Validation:** Response is either an empty collection or a string containing "error", "no holdings", "not found", or similar. No crash.

**Cleanup:** None.

---

## Test 2.4 — get_account_holdings: Invalid Account ID

**Tool call:**
```
get_account_holdings(account_id = "invalid-id-00000000")
```

**Expected:** A graceful error string. Should not crash or raise an unhandled exception.

**Validation:** Response is a string indicating an error. No unhandled exception.

**Cleanup:** None.

---

## Test 2.5 — refresh_accounts: Happy Path

**Note:** Run this test LAST in the phase because it triggers real institution refresh calls.

**Tool call:**
```
refresh_accounts()
```

**Expected:** A success response indicating the refresh was requested. May return a confirmation string or a success dict.

**Validation:** Response indicates success (not an error). Contains "success", "refresh", "requested", or similar (case-insensitive), OR is a dict/structured response without error indicators.

**Cleanup:** None. (The refresh happens asynchronously on Monarch's side.)
