# Phase 10 — Read-Only Tools (12 tests)

## 10.1 — get_transactions_summary: returns aggregate stats
Call `get_transactions_summary()`.
**Expected:** JSON response with summary data (count, sum, or similar aggregation fields).

## 10.2 — get_subscription_details: returns subscription info
Call `get_subscription_details()`.
**Expected:** JSON with subscription details including at least one of: `id`, `paymentSource`, `hasPremiumEntitlement`.

## 10.3 — get_institutions: returns connected institutions
Call `get_institutions()`.
**Expected:** JSON with institution/credential data. May have `credentials` key with a list.

## 10.4 — get_cashflow_summary: no dates
Call `get_cashflow_summary()`.
**Expected:** JSON with cashflow summary data.

## 10.5 — get_cashflow_summary: with dates
Call `get_cashflow_summary(start_date="2025-01-01", end_date="2025-01-31")`.
**Expected:** JSON with cashflow summary for the specified period.

## 10.6 — get_cashflow_summary: only start_date -> error
Call `get_cashflow_summary(start_date="2025-01-01")`.
**Expected:** JSON with `error` key about requiring both dates.

## 10.7 — get_recurring_transactions: no dates
Call `get_recurring_transactions()`.
**Expected:** JSON with recurring transaction data.

## 10.8 — get_recurring_transactions: with dates
Call `get_recurring_transactions(start_date="2025-01-01", end_date="2025-12-31")`.
**Expected:** JSON with recurring transaction data for the period.

## 10.9 — get_recurring_transactions: only end_date -> error
Call `get_recurring_transactions(end_date="2025-12-31")`.
**Expected:** JSON with `error` key.

## 10.10 — find_merchant_id_by_name: returns distinct merchants
Call `find_merchant_id_by_name(name="amazon")` (substitute any merchant name likely to appear in your transactions; fallback: pick a name from a recent `get_transactions(limit=10)` result).
**Expected:** JSON array. Each entry has `merchant_id`, `merchant_name`, plus optional `sample_amount`, `sample_date`, `sample_account`. IDs are distinct (no duplicates within the array).

**Validation:**
- Response is a JSON list (may be empty if the search yields no matches).
- Every entry includes a non-null `merchant_id`.
- No `merchant_id` appears twice.

## 10.11 — find_merchant_id_by_name: respects limit
Call `find_merchant_id_by_name(name="amazon", limit=1)` (use the same query as 10.10).
**Expected:** JSON array with at most 1 entry.

**Validation:** `len(result) <= 1`.

## 10.12 — find_merchant_id_by_name: empty for nonsense query
Call `find_merchant_id_by_name(name="zzzz-no-such-merchant-zzzz")`.
**Expected:** Empty JSON array `[]`. No crash.

**Validation:** Response parses as a list with length 0.
