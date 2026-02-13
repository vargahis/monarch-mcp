# Phase 3 — Transaction Reads (14 tests)

All tests use `get_transactions` with various parameter combinations.

---

## Test 3.1 — No Filters (limit=10)

**Tool call:**
```
get_transactions(limit = 10)
```

**Expected:** A list of up to 10 transactions. Each transaction should have: `id`, `amount`, `date`, `merchant` (or `merchantName`), and `category` (or `categoryId`).

**Validation:**
- Response is a list.
- Length is between 1 and 10.
- Each transaction has an `id` field.

**Cleanup:** None.

---

## Test 3.2 — Date Range (Jan 2025)

**Tool call:**
```
get_transactions(start_date = "2025-01-01", end_date = "2025-01-31")
```

**Expected:** A list of transactions all dated within January 2025.

**Validation:**
- Response is a list (may be empty if no transactions in that range).
- If non-empty, every transaction's `date` field starts with "2025-01".

**Cleanup:** None.

---

## Test 3.3 — Account Filter

**Tool call:**
```
get_transactions(account_id = "{checking_account_id}", limit = 10)
```

**Expected:** A list of transactions all belonging to the specified account.

**Validation:**
- Response is a list.
- If non-empty, every transaction's account-related field matches `{checking_account_id}`.

**Cleanup:** None.

---

## Test 3.4 — Account + Date Range Combined

**Tool call:**
```
get_transactions(
  account_id = "{checking_account_id}",
  start_date = "2025-01-01",
  end_date   = "2025-01-31",
  limit      = 10
)
```

**Expected:** Transactions filtered by both account and date range.

**Validation:**
- Response is a list (may be empty).
- If non-empty, all transactions match the account and have dates in January 2025.

**Cleanup:** None.

---

## Test 3.5 — Only start_date (Missing end_date)

**Tool call:**
```
get_transactions(start_date = "2025-01-01")
```

**Expected:** An error message indicating both start_date and end_date are required.

**Validation:** Response is a string containing "both" or "required" or "end_date" (case-insensitive).

**Cleanup:** None.

---

## Test 3.6 — Only end_date (Missing start_date)

**Tool call:**
```
get_transactions(end_date = "2025-01-31")
```

**Expected:** An error message indicating both start_date and end_date are required.

**Validation:** Response is a string containing "both" or "required" or "start_date" (case-insensitive).

**Cleanup:** None.

---

## Test 3.7 — Pagination: offset=0 vs offset=5

**Tool calls:**
```
get_transactions(limit = 5, offset = 0)
get_transactions(limit = 5, offset = 5)
```

**Expected:** Two sets of transactions with no overlapping IDs.

**Validation:**
- Both responses are lists.
- Extract IDs from both sets.
- The two sets of IDs have zero intersection.

**Cleanup:** None.

---

## Test 3.8 — Large Offset (999999)

**Tool call:**
```
get_transactions(limit = 10, offset = 999999)
```

**Expected:** An empty list (offset beyond available transactions).

**Validation:** Response is an empty list or contains zero transactions. No crash.

**Cleanup:** None.

---

## Test 3.9 — limit=0

**Tool call:**
```
get_transactions(limit = 0)
```

**Expected:** An empty list or the API's default behavior. No crash.

**Validation:** Response is a list (empty or not) or an error message. No crash or unhandled exception.

**Cleanup:** None.

---

## Test 3.10 — Negative Limit (-1)

**Tool call:**
```
get_transactions(limit = -1)
```

**Expected:** A graceful error message or empty list. No crash.

**Validation:** Response does not indicate an unhandled exception. Either a list, empty list, or error string.

**Cleanup:** None.

---

## Test 3.11 — Negative Offset (-1)

**Tool call:**
```
get_transactions(limit = 10, offset = -1)
```

**Expected:** A graceful error or normal results. No crash.

**Validation:** Response does not indicate an unhandled exception. Either a list or error string.

**Cleanup:** None.

---

## Test 3.12 — Very Large Limit (10000)

**Tool call:**
```
get_transactions(limit = 10000)
```

**Expected:** Either returns a list of transactions or a graceful error. The Monarch API rejects very large limits silently.

**Validation:** Response is either a list OR an error string. No crash or unhandled exception.

**Cleanup:** None.

---

## Test 3.13 — Invalid Date Format

**Tool call:**
```
get_transactions(start_date = "not-a-date", end_date = "also-not-a-date")
```

**Expected:** A graceful error string indicating invalid date format.

**Validation:** Response is a string containing "error", "invalid", "format", "date", or "parse" (case-insensitive).

**Cleanup:** None.

---

## Test 3.14 — Future Dates (2030)

**Tool call:**
```
get_transactions(start_date = "2030-01-01", end_date = "2030-12-31")
```

**Expected:** An empty list (no transactions exist in 2030).

**Validation:** Response is an empty list or a list with zero items. No crash.

**Cleanup:** None.
