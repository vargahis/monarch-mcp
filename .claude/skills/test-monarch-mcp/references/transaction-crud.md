# Phase 6 — Transaction CRUD (16 tests)

> **Scope:** Happy create/update/delete paths plus one representative invalid-id error. Adversarial
> create/update inputs (invalid account/category/date, huge amounts, unicode, 1000-char notes, XSS
> merchants) and delete error paths live in the live e2e suite
> (`tests/integration/test_transactions_live.py`).

**Important:** After every successful `create_transaction` call, immediately append the returned transaction ID to `created_resources.transactions` in the state file before running the next test.

---

## Create Tests (4 tests)

### Test 6.1 — create_transaction: Happy Path

**Tool call:**
```
create_transaction(
  account_id    = "{checking_account_id}",
  amount        = -15.50,
  merchant_name = "MCP-Test-Coffee-Shop",
  category_id   = "{valid_category_id}",
  date          = "2025-06-15",
  notes         = "Test transaction created by MCP test skill"
)
```

**Expected:** Returns a transaction object with all fields populated: `id`, `amount`, `merchant` or `merchantName`, `date`, `category`.

**Validation:**
- Response contains an `id` field.
- `amount` is -15.50 (or close to it).
- Merchant name matches or contains "MCP-Test-Coffee-Shop".

**Immediately after:** Add the returned `id` to `created_resources.transactions`. Save as `{created_txn_id}` for later tests.

---

### Test 6.2 — create_transaction: Positive Amount (Income)

**Tool call:**
```
create_transaction(
  account_id    = "{checking_account_id}",
  amount        = 100.00,
  merchant_name = "MCP-Test-Income",
  category_id   = "{valid_category_id}",
  date          = "2025-06-15"
)
```

**Expected:** Transaction created successfully with positive amount.

**Validation:** Response contains an `id` field. Amount is positive.

**Immediately after:** Add ID to `created_resources.transactions`.

---

### Test 6.3 — create_transaction: Without Optional Notes

**Tool call:**
```
create_transaction(
  account_id    = "{checking_account_id}",
  amount        = -5.00,
  merchant_name = "MCP-Test-No-Notes",
  category_id   = "{valid_category_id}",
  date          = "2025-06-15"
)
```

**Expected:** Transaction created; notes field is empty/null.

**Validation:** Response contains an `id` field. No crash.

**Immediately after:** Add ID to `created_resources.transactions`.

---

### Test 6.4 — create_transaction: Amount = 0

**Tool call:**
```
create_transaction(
  account_id    = "{checking_account_id}",
  amount        = 0,
  merchant_name = "MCP-Test-Zero-Amount",
  category_id   = "{valid_category_id}",
  date          = "2025-06-15"
)
```

**Expected:** Either succeeds or returns a graceful error about zero amount.

**Validation:** Response is either a valid transaction with `id`, or an error string. No crash.

**Cleanup:** If created, add ID to `created_resources.transactions`.

---

## Update Tests (11 tests)

All update tests use `{test_transaction_id}` from discovery. After all update tests, the original values will be restored during cleanup.

### Test 6.5 — update_transaction: Update Notes

**Tool call:**
```
update_transaction(
  transaction_id = "{test_transaction_id}",
  notes          = "MCP-Test-Updated notes"
)
```

**Expected:** Response reflects the updated notes.

**Validation:** Response indicates success. Notes field contains "MCP-Test-Updated notes".

---

### Test 6.6 — update_transaction: No-op (Only transaction_id)

**Tool call:**
```
update_transaction(
  transaction_id = "{test_transaction_id}"
)
```

**Expected:** Succeeds without making changes. The transaction remains unchanged.

**Validation:** Response indicates success (not an error). No crash.

---

### Test 6.7 — update_transaction: Update Amount

**Tool call:**
```
update_transaction(
  transaction_id = "{test_transaction_id}",
  amount         = -99.99
)
```

**Expected:** Response reflects the new amount.

**Validation:** Response indicates success. Amount field is -99.99.

---

### Test 6.8 — update_transaction: Update Merchant Name

**Tool call:**
```
update_transaction(
  transaction_id = "{test_transaction_id}",
  merchant_name  = "MCP-Test-Updated-Merchant"
)
```

**Expected:** Response reflects the new merchant name.

**Validation:** Response indicates success. Merchant field contains "MCP-Test-Updated-Merchant".

---

### Test 6.9 — update_transaction: Update Date

**Tool call:**
```
update_transaction(
  transaction_id = "{test_transaction_id}",
  date           = "2025-07-04"
)
```

**Expected:** Response reflects the new date.

**Validation:** Response indicates success. Date field contains "2025-07-04".

---

### Test 6.10 — update_transaction: Toggle hide_from_reports=true

**Tool call:**
```
update_transaction(
  transaction_id    = "{test_transaction_id}",
  hide_from_reports = true
)
```

**Expected:** Response reflects `hide_from_reports` = true.

**Validation:** Response indicates success. The `hideFromReports` or `hide_from_reports` field is true.

---

### Test 6.11 — update_transaction: Toggle needs_review=false

**Tool call:**
```
update_transaction(
  transaction_id = "{test_transaction_id}",
  needs_review   = false
)
```

**Expected:** Response reflects `needs_review` = false.

**Validation:** Response indicates success. The `needsReview` or `needs_review` field is false.

---

### Test 6.12 — update_transaction: Multiple Fields at Once

**Tool call:**
```
update_transaction(
  transaction_id = "{test_transaction_id}",
  merchant_name  = "MCP-Test-Multi-Update",
  amount         = -42.00,
  notes          = "MCP-Test-Multi-field update test"
)
```

**Expected:** All three fields updated in a single call.

**Validation:** Response indicates success. Merchant, amount, and notes all reflect new values.

---

### Test 6.13 — update_transaction: Update category_id

**Tool call:**
```
update_transaction(
  transaction_id = "{test_transaction_id}",
  category_id    = "{valid_category_id}"
)
```

**Expected:** Category updated (or unchanged if already this category).

**Validation:** Response indicates success. Category field matches `{valid_category_id}`.

---

### Test 6.14 — update_transaction: Clear Notes via clear_notes Flag

**Tool call:**
```
update_transaction(
  transaction_id = "{test_transaction_id}",
  clear_notes    = true
)
```

**Expected:** The notes field is cleared (empty). `clear_notes=true` is the client-friendly way to clear notes without passing an empty string.

**Validation:** Response indicates success (not an error). The `notes` field is empty/null. No crash.

---

### Test 6.15 — update_transaction: Invalid transaction_id

**Tool call:**
```
update_transaction(
  transaction_id = "invalid-txn-id-00000",
  notes          = "This should fail"
)
```

**Expected:** A graceful error indicating the transaction was not found.

**Validation:** Response is an error string. No unhandled exception.

---

## Delete Tests (1 test)

### Test 6.16 — delete_transaction: Happy Path

**Prerequisite:** `{created_txn_id}` from test 6.1 must exist.

**Tool call:**
```
delete_transaction(transaction_id = "{created_txn_id}")
```

**Expected:** Success response: `{deleted: true}` or confirmation string.

**Validation:** Response indicates successful deletion.

**Immediately after:** Remove `{created_txn_id}` from `created_resources.transactions`.
