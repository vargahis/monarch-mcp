# Phase 4 — Budgets & Cashflow (12 tests)

---

## Test 4.1 — get_budgets: Both Dates (Jan 2025)

**Tool call:**
```
get_budgets(start_date = "2025-01-01", end_date = "2025-01-31")
```

**Expected:** A dict containing budget data. Look for a key like `budgetData`, `budget`, or similar structured response.

**Validation:** Response is a dict/structured object (not an error string). Contains budget-related keys.

**Cleanup:** None.

---

## Test 4.2 — get_budgets: No Dates (Defaults)

**Tool call:**
```
get_budgets()
```

**Expected:** A non-empty dict with budget data using the tool's default date range.

**Validation:** Response is a dict/structured object (not an error string). Non-empty.

**Cleanup:** None.

---

## Test 4.3 — get_budgets: Only start_date

**Tool call:**
```
get_budgets(start_date = "2025-01-01")
```

**Expected:** An error message indicating both dates are required.

**Validation:** Response is a string containing "both" or "required" or "end_date" (case-insensitive).

**Cleanup:** None.

---

## Test 4.4 — get_budgets: Only end_date

**Tool call:**
```
get_budgets(end_date = "2025-01-31")
```

**Expected:** An error message indicating both dates are required.

**Validation:** Response is a string containing "both" or "required" or "start_date" (case-insensitive).

**Cleanup:** None.

---

## Test 4.5 — get_budgets: Invalid Date Format

**Tool call:**
```
get_budgets(start_date = "not-a-date", end_date = "also-not-a-date")
```

**Expected:** A graceful error string indicating invalid date format.

**Validation:** Response is a string containing "error", "invalid", "format", or "date" (case-insensitive).

**Cleanup:** None.

---

## Test 4.6 — get_budgets: Future Dates (2030)

**Tool call:**
```
get_budgets(start_date = "2030-01-01", end_date = "2030-12-31")
```

**Expected:** A dict response, possibly with empty/zero budget data. Should not crash.

**Validation:** Response is a dict/structured object (not an error string). No crash.

**Cleanup:** None.

---

## Test 4.7 — get_cashflow: Both Dates (Jan 2025)

**Tool call:**
```
get_cashflow(start_date = "2025-01-01", end_date = "2025-01-31")
```

**Expected:** A dict containing cashflow summary data. Look for a `summary` key or income/expense fields.

**Validation:** Response is a dict/structured object (not an error string). Contains cashflow-related keys.

**Cleanup:** None.

---

## Test 4.8 — get_cashflow: No Dates (Defaults)

**Tool call:**
```
get_cashflow()
```

**Expected:** A dict with cashflow data using the tool's default date range (current month).

**Validation:** Response is a dict/structured object (not an error string). Contains cashflow-related keys.

**Cleanup:** None.

---

## Test 4.9 — get_cashflow: Only start_date

**Tool call:**
```
get_cashflow(start_date = "2025-01-01")
```

**Expected:** An error message indicating both dates are required.

**Validation:** Response is a string containing "both" or "required" or "end_date" (case-insensitive).

**Cleanup:** None.

---

## Test 4.10 — get_cashflow: Only end_date

**Tool call:**
```
get_cashflow(end_date = "2025-01-31")
```

**Expected:** An error message indicating both dates are required.

**Validation:** Response is a string containing "both" or "required" or "start_date" (case-insensitive).

**Cleanup:** None.

---

## Test 4.11 — get_cashflow: Invalid Date Format

**Tool call:**
```
get_cashflow(start_date = "not-a-date", end_date = "also-not-a-date")
```

**Expected:** A graceful error string indicating invalid date format.

**Validation:** Response is a string containing "error", "invalid", "format", or "date" (case-insensitive).

**Cleanup:** None.

---

## Test 4.12 — get_cashflow: Future Dates (2030)

**Tool call:**
```
get_cashflow(start_date = "2030-01-01", end_date = "2030-12-31")
```

**Expected:** A dict with cashflow data, likely showing zero sums for income and expenses.

**Validation:** Response is a dict/structured object (not an error string). No crash.

**Cleanup:** None.
