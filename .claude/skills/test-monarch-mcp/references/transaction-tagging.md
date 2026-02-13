# Phase 7 — Transaction Tagging (5 tests)

This phase tests `set_transaction_tags` by creating temporary test tags, applying them to the test transaction, and cleaning up.

**Setup:** Before running tests, create two temporary tags:
```
create_transaction_tag(name = "MCP-Test-TagA", color = "#AA0000")
create_transaction_tag(name = "MCP-Test-TagB", color = "#00AA00")
```
Record both IDs as `tag_a_id` and `tag_b_id`. Add both to `created_resources.tags` immediately.

---

## Test 7.1 — set_transaction_tags: Apply Single Tag

**Tool call:**
```
set_transaction_tags(
  transaction_id = "{test_transaction_id}",
  tag_ids        = ["{tag_a_id}"]
)
```

**Expected:** Success response indicating the tag was applied.

**Validation:** Response indicates success. No error.

---

## Test 7.2 — set_transaction_tags: Apply Multiple Tags

**Tool call:**
```
set_transaction_tags(
  transaction_id = "{test_transaction_id}",
  tag_ids        = ["{tag_a_id}", "{tag_b_id}"]
)
```

**Expected:** Success response indicating both tags were applied.

**Validation:** Response indicates success. No error.

---

## Test 7.3 — set_transaction_tags: Remove All Tags (Empty List)

**Tool call:**
```
set_transaction_tags(
  transaction_id = "{test_transaction_id}",
  tag_ids        = []
)
```

**Expected:** Success response. All tags removed from the transaction.

**Validation:** Response indicates success. No error.

---

## Test 7.4 — set_transaction_tags: Invalid transaction_id

**Tool call:**
```
set_transaction_tags(
  transaction_id = "invalid-txn-id-00000",
  tag_ids        = ["{tag_a_id}"]
)
```

**Expected:** A graceful error indicating the transaction was not found.

**Validation:** Response is an error string. No unhandled exception.

---

## Test 7.5 — set_transaction_tags: Non-Existent tag_id

**Tool call:**
```
set_transaction_tags(
  transaction_id = "{test_transaction_id}",
  tag_ids        = ["non-existent-tag-id-00000"]
)
```

**Expected:** A graceful error, or the API silently ignores the invalid tag ID.

**Validation:** Either an error string or a success response (observation test — record what happens). No crash.

**Cleanup note:** After this test, run `set_transaction_tags(transaction_id = "{test_transaction_id}", tag_ids = [])` to clear any tags that may have been applied.
