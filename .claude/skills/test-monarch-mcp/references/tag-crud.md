# Phase 5 — Tag CRUD (5 tests)

> **Read-only mode:** Run test 5.1 only. Skip 5.2-5.5 (create/delete tag requires write mode).

> **Scope:** Happy create/delete + one validation error + the duplicate-name behavior check.
> Adversarial names (unicode, 200+ chars, special characters) and delete error paths (invalid /
> already-deleted ids) live in the live e2e suite (`tests/integration/test_tags_live.py`).

**Important:** After every successful `create_transaction_tag` call, immediately append the returned tag ID to `created_resources.tags` in the state file before running the next test.

---

## Test 5.1 — get_transaction_tags: List All Tags

**Tool call:**
```
get_transaction_tags()
```

**Expected:** A list of tags (may be empty if no tags exist). Each tag should have `id`, `name`, and `color` fields.

**Validation:** Response is a list. If non-empty, each item has `id` and `name` fields.

**Cleanup:** None.

---

## Test 5.2 — create_transaction_tag: Happy Path

**Tool call:**
```
create_transaction_tag(name = "MCP-Test-Tag", color = "#FF5733")
```

**Expected:** Returns a tag object with `id`, `name` = "MCP-Test-Tag", and `color` = "#FF5733".

**Validation:**
- Response contains an `id` field.
- `name` matches "MCP-Test-Tag".
- `color` matches "#FF5733" (case-insensitive).

**Immediately after:** Add the returned `id` to `created_resources.tags`. Save this ID as `{created_tag_id}` for use in tests 5.4 and 5.5.

**Cleanup:** Will be deleted in cleanup phase.

---

## Test 5.3 — create_transaction_tag: Invalid Color ("red")

**Tool call:**
```
create_transaction_tag(name = "MCP-Test-BadColor", color = "red")
```

**Expected:** A validation error indicating the color format is invalid.

**Validation:** Response is a string containing "error", "invalid", "color", "hex", or "format" (case-insensitive).

**Cleanup:** If a tag was created despite the error, add its ID to `created_resources.tags`.

---

## Test 5.4 — create_transaction_tag: Duplicate Name

**Tool call:**
```
create_transaction_tag(name = "MCP-Test-Tag", color = "#33FF57")
```

**Note:** This uses the same name as test 5.2 but a different color.

**Expected:** Observe behavior — either:
- The API rejects duplicates (error string), OR
- The API allows duplicates (returns a new tag with a different ID).

**Validation:** Either an error string OR a valid tag object with an `id`. This is an observation test — record what happens.

**Cleanup:** If a tag was created, add its ID to `created_resources.tags`.

---

## Test 5.5 — delete_transaction_tag: Happy Path

**Prerequisite:** `{created_tag_id}` from test 5.2 must exist.

**Tool call:**
```
delete_transaction_tag(tag_id = "{created_tag_id}")
```

**Expected:** A success response, typically `{deleted: true}` or a confirmation string.

**Validation:** Response indicates successful deletion. Contains "deleted", "success", or `true`.

**Cleanup:** Remove `{created_tag_id}` from `created_resources.tags` (already deleted).
