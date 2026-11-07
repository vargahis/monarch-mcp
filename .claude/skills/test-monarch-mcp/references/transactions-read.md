# Phase 3 — Transaction Reads (9 tests)

All tests use `get_transactions` with various parameter combinations.

> **Scope:** This phase covers agent-correctness (right params, correct response handling) and one
> representative validation error. Adversarial inputs (extreme/negative/zero pagination, invalid date
> formats) live in the live e2e suite (`tests/integration/`), not here.

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

## Test 3.6 — Pagination: offset=0 vs offset=5

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

## Test 3.7 — Future Dates (2030)

**Tool call:**
```
get_transactions(start_date = "2030-01-01", end_date = "2030-12-31")
```

**Expected:** An empty list (no transactions exist in 2030).

**Validation:** Response is an empty list or a list with zero items. No crash.

**Cleanup:** None.

---

## Test 3.8 — needs_review=True Filter

**Tool call:**
```
get_transactions(needs_review = True)
```

**Expected:** A list of transactions that are flagged for review. May be empty if no transactions need review.

**Validation:** Response is a list (possibly empty). No crash or error string.

**Cleanup:** None.

---

## Test 3.9 — needs_review=False Filter

**Tool call:**
```
get_transactions(needs_review = False)
```

**Expected:** A list of transactions that do NOT need review.

**Validation:** Response is a non-empty list (most transactions should not need review). No crash or error string.

**Cleanup:** None.
