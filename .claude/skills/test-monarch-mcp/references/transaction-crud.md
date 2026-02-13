# Phase 6 — Transaction CRUD (25 tests)

**Important:** After every successful `create_transaction` call, immediately append the returned transaction ID to `created_resources.transactions` in the state file before running the next test.

---

## Create Tests (9 tests)

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

### Test 6.4 — create_transaction: Invalid account_id

**Tool call:**
```
create_transaction(
  account_id    = "invalid-account-id-00000",
  amount        = -10.00,
  merchant_name = "MCP-Test-BadAccount",
  category_id   = "{valid_category_id}",
  date          = "2025-06-15"
)
```

**Expected:** A graceful error indicating the account was not found.

**Validation:** Response is an error string. No unhandled exception.

**Cleanup:** If somehow created, add ID to `created_resources.transactions`.

---

### Test 6.5 — create_transaction: Invalid category_id

**Tool call:**
```
create_transaction(
  account_id    = "{checking_account_id}",
  amount        = -10.00,
  merchant_name = "MCP-Test-BadCategory",
  category_id   = "invalid-category-id-00000",
  date          = "2025-06-15"
)
```

**Expected:** A graceful error, or the transaction is created with the invalid category (API-dependent).

**Validation:** Either an error string or a valid transaction object. No crash.

**Cleanup:** If created, add ID to `created_resources.transactions`.

---

### Test 6.6 — create_transaction: Invalid Date

**Tool call:**
```
create_transaction(
  account_id    = "{checking_account_id}",
  amount        = -10.00,
  merchant_name = "MCP-Test-BadDate",
  category_id   = "{valid_category_id}",
  date          = "not-a-date"
)
```

**Expected:** A graceful error about invalid date format.

**Validation:** Response is a string containing "error", "invalid", "date", or "format" (case-insensitive).

**Cleanup:** If somehow created, add ID to `created_resources.transactions`.

---

### Test 6.7 — create_transaction: Amount = 0

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

### Test 6.8 — create_transaction: Very Large Amount

**Tool call:**
```
create_transaction(
  account_id    = "{checking_account_id}",
  amount        = -999999999.99,
  merchant_name = "MCP-Test-Large-Amount",
  category_id   = "{valid_category_id}",
  date          = "2025-06-15"
)
```

**Expected:** Either succeeds or returns a graceful error about amount limits.

**Validation:** Response is either a valid transaction with `id`, or an error string. No crash.

**Cleanup:** If created, add ID to `created_resources.transactions`.

---

### Test 6.9 — create_transaction: Unicode Merchant

**Tool call:**
```
create_transaction(
  account_id    = "{checking_account_id}",
  amount        = -8.00,
  merchant_name = "MCP-Test-カフェ-☕",
  category_id   = "{valid_category_id}",
  date          = "2025-06-15"
)
```

**Expected:** Either succeeds (unicode stored) or returns a graceful error.

**Validation:** Response is either a valid transaction with `id`, or an error string. No crash.

**Cleanup:** If created, add ID to `created_resources.transactions`.

---

## Update Tests (13 tests)

All update tests use `{test_transaction_id}` from discovery. After all update tests, the original values will be restored during cleanup.

### Test 6.10 — update_transaction: Update Notes

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

### Test 6.11 — update_transaction: No-op (Only transaction_id)

**Tool call:**
```
update_transaction(
  transaction_id = "{test_transaction_id}"
)
```

**Expected:** Succeeds without making changes. The transaction remains unchanged.

**Validation:** Response indicates success (not an error). No crash.

---

### Test 6.12 — update_transaction: Update Amount

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

### Test 6.13 — update_transaction: Update Merchant Name

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

### Test 6.14 — update_transaction: Update Date

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

### Test 6.15 — update_transaction: Toggle hide_from_reports=true

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

### Test 6.16 — update_transaction: Toggle needs_review=false

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

### Test 6.17 — update_transaction: Multiple Fields at Once

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

### Test 6.18 — update_transaction: Update category_id

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

### Test 6.19 — update_transaction: Invalid transaction_id

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

### Test 6.20 — update_transaction: Invalid Date Format

**Tool call:**
```
update_transaction(
  transaction_id = "{test_transaction_id}",
  date           = "not-a-valid-date"
)
```

**Expected:** A graceful error about invalid date format.

**Validation:** Response is a string containing "error", "invalid", "date", or "format" (case-insensitive).

---

### Test 6.21 — update_transaction: Very Long Notes (1000+ chars)

**Tool call:**
```
update_transaction(
  transaction_id = "{test_transaction_id}",
  notes          = "MCP-Test-" + "X" * 1000
)
```

Use notes that are "MCP-Test-" followed by 1000 "X" characters (total ~1009 chars).

**Expected:** Either succeeds or returns a graceful error about length.

**Validation:** Response is either a success indicator or an error string. No crash.

---

### Test 6.22 — update_transaction: HTML in Merchant

**Tool call:**
```
update_transaction(
  transaction_id = "{test_transaction_id}",
  merchant_name  = "MCP-Test-<script>alert('xss')</script>"
)
```

**Expected:** Either succeeds (HTML stored literally) or Monarch's WAF returns a 403 blocking `<script>` tags. Both outcomes are acceptable — the important thing is no unhandled crash or false auth error.

**Validation:** Response is either a success indicator with the merchant field set, OR an error string containing "403" or "Forbidden". No crash or unhandled exception.

---

## Delete Tests (3 tests)

### Test 6.23 — delete_transaction: Happy Path

**Prerequisite:** `{created_txn_id}` from test 6.1 must exist.

**Tool call:**
```
delete_transaction(transaction_id = "{created_txn_id}")
```

**Expected:** Success response: `{deleted: true}` or confirmation string.

**Validation:** Response indicates successful deletion.

**Immediately after:** Remove `{created_txn_id}` from `created_resources.transactions`.

---

### Test 6.24 — delete_transaction: Invalid ID

**Tool call:**
```
delete_transaction(transaction_id = "invalid-txn-id-00000")
```

**Expected:** A graceful error indicating the transaction was not found.

**Validation:** Response is an error string. No unhandled exception.

---

### Test 6.25 — delete_transaction: Already-Deleted ID

**Prerequisite:** `{created_txn_id}` from test 6.1 was deleted in test 6.23.

**Tool call:**
```
delete_transaction(transaction_id = "{created_txn_id}")
```

**Expected:** Either a graceful error indicating the transaction no longer exists, or an idempotent success (`deleted: true`). The Monarch API treats delete as idempotent.

**Validation:** Response is an error string, "not found" / "already deleted", OR `{deleted: true}`. No crash.
