# Phase 14 — Recurring Merchant Management (5 tests)

**Read-only mode:** Run test 14.1 only (1 test). Skip 14.2-14.5 (`update_recurring_merchant` requires write mode).

This phase exercises the merchant-level recurring management tools that back Monarch's "Recurring transactions" list. The flow is: discover a merchant ID via `find_merchant_id_by_name`, then mutate it via `update_recurring_merchant`.

**Pick a safe target merchant.** Prefer a merchant that is **not** already in `get_recurring_transactions`, so the test starts from a clean non-recurring baseline and the self-cleanup at the end fully restores it. Before mutating, record the merchant's original `is_recurring` state so the Self-cleanup step can revert it.

---

## 14.1 — find_merchant_id_by_name: discover the test merchant

**Pre-requisite:** Pick a merchant name that appears in your account's recent transactions. If you ran Phase 3, reuse a merchant name from those results.

**Tool call:**
```
find_merchant_id_by_name(name = "{merchant_query}", limit = 5)
```

**Expected:** JSON array with at least one entry. Each entry has `merchant_id`, `merchant_name`, and optional sample fields.

**Validation:**
- Response is a JSON list.
- The first entry has a non-empty `merchant_id`.
- All `merchant_id` values are distinct.

**Immediately after:** Save the first entry's `merchant_id` and `merchant_name` as `{recurring_merchant_id}` and `{recurring_merchant_name}` for the remaining tests. Note whether this merchant is currently listed by `get_recurring_transactions` (its original `is_recurring` state) so the Self-cleanup step can restore it.

---

## 14.2 — update_recurring_merchant: mark merchant as recurring (write only)

**Tool call:**
```
update_recurring_merchant(
  merchant_id  = "{recurring_merchant_id}",
  name         = "{recurring_merchant_name}",
  is_recurring = true,
  frequency    = "monthly",
  base_date    = "2025-01-15",
  amount       = -9.99,
  is_active    = true
)
```

**Expected:** JSON response with an `updateMerchant` (or similar) key containing the updated merchant. No `errors`.

**Validation:** Response indicates success. The merchant's `id` matches `{recurring_merchant_id}`.

---

## 14.3 — update_recurring_merchant: deactivate the recurrence (write only)

> **Note:** `is_recurring` is **required** on every call. Adjusting an existing recurrence (here,
> switching it off) keeps `is_recurring=true` and passes only the field being changed — Monarch keeps
> the rest of the schedule. Omitting `is_recurring` is what produced the opaque "Something went wrong"
> error before the fix.

**Tool call:**
```
update_recurring_merchant(
  merchant_id  = "{recurring_merchant_id}",
  name         = "{recurring_merchant_name}",
  is_recurring = true,
  is_active    = false
)
```

**Expected:** Response indicates success. The merchant's recurring entry stays defined but is no longer surfaced as an active bill (`recurringTransactionStream.isActive` is false).

**Validation:** Response is a non-error JSON object.

---

## 14.4 — update_recurring_merchant: reactivate and adjust amount (write only)

**Tool call:**
```
update_recurring_merchant(
  merchant_id  = "{recurring_merchant_id}",
  name         = "{recurring_merchant_name}",
  is_recurring = true,
  is_active    = true,
  amount       = -12.49
)
```

**Expected:** Response indicates success. The recurrence is active again with the new amount; the unchanged frequency/base_date are preserved by Monarch.

**Validation:** Response is a non-error JSON object.

---

## 14.5 — update_recurring_merchant: clear the recurring flag (write only)

**Tool call:**
```
update_recurring_merchant(
  merchant_id  = "{recurring_merchant_id}",
  name         = "{recurring_merchant_name}",
  is_recurring = false
)
```

**Expected:** Response indicates success. The merchant no longer appears as a recurring bill.

**Validation:** Response is a non-error JSON object.

---

## Self-cleanup (write mode)

After the tests, restore the test merchant to the original `is_recurring` state captured in 14.1:

- **Originally non-recurring** (the recommended target): 14.5 already left it non-recurring — no further action needed. Confirm it is absent from `get_recurring_transactions`.
- **Originally recurring** (only if no non-recurring merchant was available): best-effort re-flag it with `update_recurring_merchant(merchant_id=..., name=..., is_recurring=true, is_active=true)`. The pre-test frequency/base_date/amount are not recoverable from the read tools, so note any residual change in the return so the orchestrator can warn the user.

Report the restore outcome in the subagent's `self_cleanup` field.
