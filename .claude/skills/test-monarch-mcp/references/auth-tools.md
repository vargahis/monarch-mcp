# Phase 1 — Auth Tools (3 tests)

These tools require no parameters and return informational strings.

---

## Test 1.1 — check_auth_status: Happy Path

**Tool call:**
```
check_auth_status()
```

**Expected:** A string response containing the word "token" (case-insensitive). The response should indicate whether a token is stored and its status.

**Validation:** Response is a non-empty string. Check that it contains "token" (case-insensitive).

**Cleanup:** None.

---

## Test 1.2 — debug_session_loading: Happy Path

**Tool call:**
```
debug_session_loading()
```

**Expected:** A string containing information about token length or token loading status. Look for a numeric value indicating token length, or words like "length", "loaded", "bytes", "characters", or "token".

**Validation:** Response is a non-empty string. Check that it contains at least one of: a number, "length", "loaded", "token", "keyring", "session".

**Cleanup:** None.

---

## Test 1.3 — setup_authentication: Happy Path

**Tool call:**
```
setup_authentication()
```

**Expected:** A multi-line instruction string explaining how to authenticate. Should contain setup or authentication instructions.

**Validation:** Response is a non-empty string with multiple lines (contains at least one newline or is longer than 50 characters). Should mention "auth", "login", "token", "browser", or "setup" (case-insensitive).

**Cleanup:** None.
