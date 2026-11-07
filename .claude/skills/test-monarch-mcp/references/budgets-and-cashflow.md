# Phase 4 — Budgets, Cashflow & Budget Amounts (10 tests)

> **Read-only mode:** Run tests 4.1-4.8 only. Skip 4.9-4.10 (set_budget_amount requires write mode).

> **Scope:** Keeps happy paths plus one representative "missing date" / "mutually exclusive args"
> validation error per tool. Other validation permutations are covered by the mocked unit tests.

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

## Test 4.4 — get_budgets: Future Dates (2030)

**Tool call:**
```
get_budgets(start_date = "2030-01-01", end_date = "2030-12-31")
```

**Expected:** A dict response, possibly with empty/zero budget data. Should not crash.

**Validation:** Response is a dict/structured object (not an error string). No crash.

**Cleanup:** None.

---

## Test 4.5 — get_cashflow: Both Dates (Jan 2025)

**Tool call:**
```
get_cashflow(start_date = "2025-01-01", end_date = "2025-01-31")
```

**Expected:** A dict containing cashflow summary data. Look for a `summary` key or income/expense fields.

**Validation:** Response is a dict/structured object (not an error string). Contains cashflow-related keys.

**Cleanup:** None.

---

## Test 4.6 — get_cashflow: No Dates (Defaults)

**Tool call:**
```
get_cashflow()
```

**Expected:** A dict with cashflow data using the tool's default date range (current month).

**Validation:** Response is a dict/structured object (not an error string). Contains cashflow-related keys.

**Cleanup:** None.

---

## Test 4.7 — get_cashflow: Only start_date

**Tool call:**
```
get_cashflow(start_date = "2025-01-01")
```

**Expected:** An error message indicating both dates are required.

**Validation:** Response is a string containing "both" or "required" or "end_date" (case-insensitive).

**Cleanup:** None.

---

## Test 4.8 — get_cashflow: Future Dates (2030)

**Tool call:**
```
get_cashflow(start_date = "2030-01-01", end_date = "2030-12-31")
```

**Expected:** A dict with cashflow data, likely showing zero sums for income and expenses.

**Validation:** Response is a dict/structured object (not an error string). No crash.

**Cleanup:** None.

---

## Test 4.9 — set_budget_amount: with category_id

Pick a `category_id` from discovery (or use `{valid_category_id}`).

**Tool call:**
```
set_budget_amount(amount=500.0, category_id={valid_category_id})
```

**Expected:** Success response.

**Validation:** Response is a dict/structured object (not an error string).

**Cleanup:** None.

---

## Test 4.10 — set_budget_amount: both IDs -> error

**Tool call:**
```
set_budget_amount(amount=100.0, category_id="cat-1", category_group_id="grp-1")
```

**Expected:** JSON with `error` key about providing exactly one.

**Validation:** Response contains "error" key with "exactly one" (case-insensitive).

**Cleanup:** None.
