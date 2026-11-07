---
name: test-monarch-mcp
description: Systematically test Monarch Money MCP tools in read-only mode (27 tools, 58 tests) or write-enabled mode (all 44 tools, 110 tests). Account-agnostic (discovers IDs at runtime) and self-cleaning (deletes everything it creates in write mode). Batches each phase into a subagent so large tool payloads stay out of the orchestrator's context.
user_invocable: true
---

# Test Monarch MCP Skill

You are the **orchestrator** of a comprehensive test suite for the Monarch Money MCP server.

You do **not** call Monarch tools yourself. Instead you dispatch a **subagent per phase** (via the
Task tool); each subagent runs that phase's tests, asserts on shape/key fields only, and returns a
compact PASS/FAIL summary. You aggregate the summaries, track created resources, drive cleanup, and
print the final report. This keeps large tool payloads (transaction lists, rule lists, full objects)
inside the subagents and out of your context.

Run tests across 14 phases, track results, and clean up after yourself.

> **Scope of this skill:** it validates that the **agent** uses the MCP tools correctly — right tool,
> right params, correct interpretation of responses (happy paths, agent-judgment cases, and one
> representative graceful-error case per tool family). It does **not** stress-test tool robustness.
> Adversarial/edge inputs and live-API error paths are covered by the deterministic e2e suite in
> `tests/integration/` (run with `MONARCH_LIVE_TESTS=1 pytest tests/integration -m integration`).

---

## Mode Support

This test suite supports two modes, auto-detected at startup:

- **Read-only mode** (default): Tests 27 read-only tools (58 tests). Write-dependent tests are
  skipped. No data is created, modified, or deleted.
- **Write-enabled mode** (`--enable-write`): Tests all 44 tools (110 tests). Creates, modifies, and
  deletes data on your live Monarch account. Self-cleaning.

---

## Execution Model

### Your job (orchestrator)

- Detect the server mode and get user confirmation (see **Pre-flight**).
- Dispatch the **discovery subagent**, then one subagent per phase, then (write mode) the **cleanup
  subagent**.
- Parse each subagent's compact JSON return. Never request or echo a raw tool payload.
- Maintain `mcp-test-state.json`; merge the created-resource IDs each subagent reports.
- Print the final summary.

### Dispatching a subagent

Use the Task tool (subagent type: `general-purpose`). The prompt you pass must contain:

1. **Mode** (`read-only` / `read-write`) and, in read-only mode, the **exact subset of tests** to run
   for this phase (from the Phase Map).
2. **Discovery values** to substitute for `{placeholder}` tokens (see Placeholder Reference).
3. **The reference file path** to read and follow (e.g. `references/transaction-crud.md`).
4. **The subagent rules and return contract** below.

### Subagent rules (include verbatim in every phase dispatch)

- Read the reference file. Run each listed test **in order**. Substitute the provided discovery
  values for any `{placeholder}` tokens.
- Call tools by their MCP name `mcp__monarch-mcp__<tool>` (e.g. `mcp__monarch-mcp__get_transactions`).
  If a tool is not directly callable, first load it with `ToolSearch` using the query
  `select:mcp__monarch-mcp__<tool>`, then call it.
- **Assert on shape / key fields only** — e.g. "response is a list", "has an `id`", "date starts with
  2025-01", "error string contains 'both'". Read only what you need from each response and discard the
  rest. **Never** copy a full tool response into your output.
- **Write phases self-clean:** after running the tests, delete any resource you created that a
  delete-test did not already remove — transactions via `delete_transaction`, tags via
  `delete_transaction_tag`, categories via `delete_transaction_category`, accounts via
  `delete_account`. Do **not** revert the shared `{test_transaction_id}` — the orchestrator owns its
  original values and reverts it during cleanup.
- Return **only** the JSON object defined below. No prose, no payloads.

### Return contract

```json
{
  "phase": 6,
  "phase_name": "Transaction CRUD",
  "summary": { "passed": 14, "failed": 1, "skipped": 0 },
  "results": [
    { "test": "6.1", "status": "PASS" },
    { "test": "6.7", "status": "FAIL",
      "detail": "expected amount -99.99; got error '<one-line msg>'; params: amount=-99.99" }
  ],
  "created_resources": { "transactions": [], "tags": [], "categories": [], "accounts": [] },
  "self_cleanup": { "deleted": ["txn:abc"], "failed": [] }
}
```

- `results`: one row per test. PASS rows carry only `test` + `status`. FAIL/SKIP rows add a one-line
  `detail` (expected vs actual + the params used, or the skip reason). No payloads.
- `created_resources`: resources the subagent created but did **not** delete itself — the orchestrator
  backstop for cleanup.
- `self_cleanup`: IDs the subagent deleted itself (transparency); `failed` lists deletions that errored.

### Dispatch strategy

- **Read-only mode:** after discovery, dispatch the phase subagents **concurrently** (several Task
  calls in one message) — they are independent and perform no writes. Aggregate as they return. No
  cleanup phase.
- **Write mode:** after discovery, dispatch the phase subagents **sequentially in phase order**
  (Phases 6 and 7 both mutate the shared test transaction, so serializing avoids races and keeps
  cleanup deterministic). After each subagent returns, merge its `created_resources` into the state
  file and record its results before dispatching the next. Then run the cleanup subagent.

### Phase Map

| Phase | Name | Reference file | Read-only subset | Mutates data |
|---|---|---|---|---|
| 0 | Discovery | (inline subagent — see Phase 0) | runs | no |
| 1 | Auth Tools | `references/auth-tools.md` | all (3) | no |
| 2 | Accounts & Holdings | `references/accounts-and-holdings.md` | all (5) | no |
| 3 | Transaction Reads | `references/transactions-read.md` | all (9) | no |
| 4 | Budgets, Cashflow & Budget Amounts | `references/budgets-and-cashflow.md` | 4.1–4.8 | yes (4.9–4.10) |
| 5 | Tag CRUD | `references/tag-crud.md` | 5.1 | yes |
| 6 | Transaction CRUD | `references/transaction-crud.md` | — (skip) | yes |
| 7 | Transaction Tagging | `references/transaction-tagging.md` | — (skip) | yes |
| 8 | Categories | `references/categories.md` | 8.1–8.3 | yes |
| 9 | Details & Splits | `references/transaction-details-and-splits.md` | 9.1–9.4 | yes (9.5–9.7) |
| 10 | Read-Only Tools | `references/read-only-tools.md` | all (12) | no |
| 11 | Account Management | `references/account-management.md` | 11.1, 11.6-alt, 11.7–11.10 | yes |
| 12 | Analytics | `references/analytics-tools.md` | all (5) | no |
| 13 | Transaction Rules | `references/transaction-rules.md` | 13.6 | yes |
| 14 | Recurring Merchant Management | `references/recurring-merchant.md` | 14.1 | yes |

> **Phase 11 read-only note:** run **11.6-alt** instead of 11.6 — it calls `get_account_history` with
> `{checking_account_id}` because no account is created in read-only mode.

---

## State File Management

The state file is `mcp-test-state.json` in the project root.

### On Invocation — Check for Existing State

1. Try to read `mcp-test-state.json`.
2. **Not found** → Start a fresh run from Phase 0.
3. **Found with `status: "in_progress"`** → Ask the user:
   - "Resume from Phase {last_completed_phase + 1}?"
   - "Clean up and start fresh?"
   - "Clean up only?"
4. **Found with `status: "cleanup_needed"`** → Dispatch the cleanup subagent with the stored IDs and
   `original_values`, then delete the state file.
5. **Found with `status: "completed"`** → Show previous results summary, ask: "Run again?" If yes,
   delete state file and start fresh.

### State File Structure

```json
{
  "status": "in_progress | completed | cleanup_needed",
  "mode": "read-only | read-write",
  "started_at": "<ISO timestamp>",
  "last_updated": "<ISO timestamp>",
  "last_completed_phase": 0,
  "discovery": {
    "checking_account_id": "",
    "investment_account_id": "",
    "test_transaction_id": "",
    "valid_category_id": "",
    "original_values": {
      "merchant": "",
      "notes": "",
      "amount": 0,
      "date": "",
      "category_id": "",
      "hide_from_reports": false,
      "needs_review": false
    }
  },
  "created_resources": {
    "transactions": [],
    "tags": [],
    "categories": [],
    "accounts": []
  },
  "results": {},
  "summary": {
    "total": 110,
    "passed": 0,
    "failed": 0,
    "skipped": 0
  }
}
```

In **read-only mode**, `summary.total` is `58` and `original_values` is omitted (no mutations happen).
In **write-enabled mode**, `summary.total` is `110`.

### Update Cadence

- **Write** the state file after the discovery subagent returns (discovery IDs and, in write mode,
  `original_values` are now logged; `status: "in_progress"`, `last_completed_phase: 0`).
- **After each phase subagent returns:** merge its reported `created_resources` into the state file,
  append its `results`, bump `last_completed_phase`, and update `summary` counts.
- Set `status: "completed"` after the cleanup subagent succeeds, then **delete** the state file.

> The state file's `created_resources` is the orchestrator backstop. Subagents self-clean their own
> creations, but the merged list plus the cleanup subagent's name-prefix sweep ensures nothing is left
> behind even if a subagent crashes without reporting.

---

## Error Handling Rules

- **Phase 0 (discovery) failure = HALT.** If discovery fails or a required ID is missing, do not
  proceed. Write the state file with `status: "cleanup_needed"` and stop.
- **All other phases: log and continue.** A subagent records `FAIL` per test and keeps going. If a
  whole subagent errors or returns a malformed object, record the phase as failed and continue —
  then ensure cleanup still runs.
- **Cleanup always runs (write mode).** Even if a phase failed or was skipped, dispatch the cleanup
  subagent.
- **Test data naming:** all test merchants, tags, categories, accounts, and rule criteria are
  prefixed with `MCP-Test-` for easy identification and for the cleanup name-prefix sweep.

---

## Pre-flight: Auto-detect Mode & Confirm

Before starting any test work (including Phase 0), detect the server mode and get user confirmation.

### Mode Detection (Phase 0 preamble)

Check which MCP tools are available. If write tools like `create_transaction`, `create_transaction_tag`,
`delete_transaction`, `update_recurring_merchant`, etc. are available, the server is in **read-write mode**.
If they are absent, the server is in **read-only mode**.

### User Confirmation

Based on the detected mode, display the appropriate message and **STOP and wait for explicit user
approval**:

#### If read-only mode detected:

---

**Server is running in read-only mode (27 tools).**

I'll run 58 read-only tests and skip 52 write tests. No data will be created, modified, or deleted on
your Monarch account.

To test all 110 tests, disable `monarch-money-read-only` and enable `monarch-money` in `.mcp.json`,
then restart.

**Proceed with read-only tests?**

---

#### If read-write mode detected:

---

**WARNING: Server is running in read-write mode (all 44 tools).**

I'll run all 110 tests. This will **create, modify, and delete** data on your **live Monarch Money
account**:

- It **creates and deletes** transactions, tags, categories, and accounts.
- It **temporarily modifies** an existing transaction and one merchant's recurring state (then reverts them).
- The test is designed to clean up everything it creates, but **if something goes wrong** (network
  error, timeout, context limit), **cleanup may be incomplete** and unwanted changes could remain in
  your account.
- All test-created data is prefixed with `MCP-Test-` for easy manual identification.
- If the session is interrupted, you can **resume where you left off** by invoking this skill again —
  it will detect the saved progress and offer to continue.

To test read-only mode only, disable `monarch-money` and enable `monarch-money-read-only` in
`.mcp.json`, then restart.

**Do you want to continue?**

---

Do NOT proceed until the user explicitly confirms. If the user declines, stop immediately.

This confirmation applies to **fresh runs only**. When resuming an in-progress run or performing
cleanup-only, skip this confirmation (the user already accepted the risk).

---

## Phase 0 — Discovery

Dispatch a **discovery subagent** first (so even discovery payloads stay out of your context). Give it
the mode and these instructions; it returns only the compact ID set below.

The discovery subagent must:

1. Call `mcp__monarch-mcp__get_accounts()`.
   - `checking_account_id`: the first account whose `type` contains "checking" (case-insensitive).
     Fallback: the first account in the list.
   - `investment_account_id`: the first account whose `type` contains "investment" or "brokerage"
     (case-insensitive). May be null if none found.
2. Call `mcp__monarch-mcp__get_transactions(limit=5)`.
   - `test_transaction_id`: the first transaction's ID.
   - `valid_category_id`: the first transaction's category ID.
3. **Write mode only:** call `mcp__monarch-mcp__get_transaction_details(transaction_id={test_transaction_id})`
   and record `original_values`: `merchant` (or `merchant_name`), `notes`, `amount`, `date`,
   `category_id`, `hide_from_reports`, `needs_review`. These are used to revert the transaction during
   cleanup.
4. Return only:

```json
{
  "checking_account_id": "...",
  "investment_account_id": "..." ,
  "test_transaction_id": "...",
  "valid_category_id": "...",
  "original_values": { "...": "... (write mode only)" }
}
```

On return, the orchestrator:

- Initializes `created_resources = { transactions: [], tags: [], categories: [], accounts: [] }`.
- Records `mode` and writes the state file with `status: "in_progress"`, `last_completed_phase: 0`.
- Prints discovery results:
  ```
  === Phase 0: Discovery ===
  Mode:                {read-only | read-write}
  Checking account:    {id}
  Investment account:  {id} or "None found"
  Test transaction:    {id}
  Valid category:      {id}
  ```

If any required value (`checking_account_id`, `test_transaction_id`, `valid_category_id`) is missing,
**HALT**.

---

## Phases 1–14

For each phase, dispatch a subagent per the **Execution Model** (read-only → concurrent; write →
sequential). Pass the mode, the read-only subset (from the Phase Map), the discovery values, the
reference file path, and the subagent rules + return contract.

After each subagent returns: merge its `created_resources` into the state file, append its `results`,
bump `last_completed_phase`, and update `summary`.

---

## Cleanup Phase

### Read-only mode

Skip cleanup entirely — no resources were created and no mutations were made. Set `status: "completed"`
in the state file, then delete `mcp-test-state.json`.

### Write mode

**This phase ALWAYS runs**, even if earlier phases failed or were skipped. Dispatch a **cleanup
subagent**, passing it `test_transaction_id`, `original_values`, and the merged `created_resources`
lists. The cleanup subagent must perform all steps below and return a compact summary.

#### Step 1: Revert the test transaction

```
update_transaction(
  transaction_id    = {test_transaction_id},
  merchant_name     = {original_values.merchant},
  notes             = {original_values.notes},
  amount            = {original_values.amount},
  date              = {original_values.date},
  category_id       = {original_values.category_id},
  hide_from_reports = {original_values.hide_from_reports},
  needs_review      = {original_values.needs_review}
)
```

> **Clearing notes:** if `original_values.notes` was null/empty, omit `notes` from the
> call above and instead pass `clear_notes=true` — `update_transaction` treats `null` as
> "leave unchanged", and `clear_notes=true` clears the field reliably (some clients cannot
> transmit the empty string that the legacy `notes=""` path requires). (Same for an unlinked
> goal: pass `clear_goal=true`.)

#### Step 2: Remove tags from the test transaction

```
set_transaction_tags(transaction_id = {test_transaction_id}, tag_ids = [])
```

#### Step 3: Delete tracked resources

For each ID in the merged `created_resources`, delete it (continue on failure, log each):
`delete_transaction`, `delete_transaction_tag`, `delete_transaction_category`, `delete_account`.

#### Step 4: Name-prefix straggler sweep (backstop)

Catch anything a subagent created but failed to report or delete. The distinctive `MCP-Test-` prefix
(Monarch lowercases rule criteria, so rules appear as `mcp-test`) makes this safe:

- `get_transaction_tags()` → delete every tag whose name starts with `MCP-Test-`.
- `get_transaction_rules()` → delete every rule whose criteria value contains `mcp-test`
  (case-insensitive). Rule IDs aren't returned by `create_transaction_rule`, so they are discovered
  here.
- `get_transactions(search="MCP-Test")` → delete every returned transaction **except**
  `{test_transaction_id}` (a pre-existing transaction — never delete it; Step 1 already reverted its
  merchant. This guard protects the user's real transaction if Step 1 ever failed).
- `get_transaction_categories()` → delete every category whose name starts with `MCP-Test-`.
- `get_accounts()` → delete every account whose name starts with `MCP-Test-`.

Continue on failure; log each deletion.

#### Step 5: Verify

Re-query `get_transaction_tags()` and `get_transaction_rules()`; confirm no `MCP-Test-` / `mcp-test`
residue. Report any remaining items so the orchestrator can warn the user.

#### Step 6: Return

The cleanup subagent returns a compact summary:

```json
{ "reverted": true, "deleted": { "transactions": 3, "tags": 4, "categories": 2, "accounts": 1, "rules": 5 }, "residual": [] }
```

On return, the orchestrator sets `status: "completed"` and deletes `mcp-test-state.json`. If `residual`
is non-empty, warn the user.

---

## Reporting

After cleanup (or after skipping cleanup in read-only mode), print a final summary by aggregating the
subagent returns.

### Read-only mode example:

```
╔══════════════════════════════════════════════════╗
║  MCP Tool Test Results Summary (read-only mode)  ║
╠══════════════════════════════════════════════════╣
║ Phase 1  — Auth Tools:        3/3  PASS          ║
║ Phase 2  — Accounts:          5/5  PASS          ║
║ Phase 3  — Transaction Reads: 9/9  PASS          ║
║ Phase 4  — Budgets/Cashflow:  8/8  PASS          ║
║ Phase 5  — Tag CRUD:          1/1  PASS          ║
║ Phase 6  — Transaction CRUD:  SKIPPED (write)    ║
║ Phase 7  — Tagging:           SKIPPED (write)    ║
║ Phase 8  — Categories:        3/3  PASS          ║
║ Phase 9  — Details/Splits:    4/4  PASS          ║
║ Phase 10 — Read-Only Tools:   12/12 PASS         ║
║ Phase 11 — Account Mgmt:      6/6  PASS          ║
║ Phase 12 — Analytics:         5/5  PASS          ║
║ Phase 13 — Rules:             1/1  PASS          ║
║ Phase 14 — Recurring Merch:   1/1  PASS          ║
╠══════════════════════════════════════════════════╣
║ TOTAL: 58 passed, 0 failed, 0 skipped           ║
║ Write tests skipped: 52 (server in read-only)    ║
╚══════════════════════════════════════════════════╝
```

### Write mode example:

```
╔══════════════════════════════════════════════════╗
║ MCP Tool Test Results Summary (read-write mode)  ║
╠══════════════════════════════════════════════════╣
║ Phase 1  — Auth Tools:        3/3  PASS          ║
║ Phase 2  — Accounts:          5/5  PASS          ║
║ Phase 3  — Transaction Reads: 9/9  PASS          ║
║ Phase 4  — Budgets/Cashflow:  10/10 PASS         ║
║ Phase 5  — Tag CRUD:          5/5  PASS          ║
║ Phase 6  — Transaction CRUD:  16/16 PASS         ║
║ Phase 7  — Tagging:           4/4  PASS          ║
║ Phase 8  — Categories:        9/9  PASS          ║
║ Phase 9  — Details/Splits:    7/7  PASS          ║
║ Phase 10 — Read-Only Tools:   12/12 PASS         ║
║ Phase 11 — Account Mgmt:      10/10 PASS         ║
║ Phase 12 — Analytics:         5/5  PASS          ║
║ Phase 13 — Transaction Rules: 10/10 PASS         ║
║ Phase 14 — Recurring Merch:   5/5  PASS          ║
╠══════════════════════════════════════════════════╣
║ TOTAL: 110 passed, 0 failed, 0 skipped          ║
╚══════════════════════════════════════════════════╝
```

If any tests failed, list each failure with:
- Test number and name
- Expected result
- Actual result
- Tool call parameters used

(All of this comes straight from the `FAIL` rows' `detail` fields — you never need the raw payloads.)

---

## Aggregating Subagent Results

You never run individual tests — you parse subagent returns. For each phase:

1. **Before dispatching**, print: `=== Phase {n}: {name} === (dispatching subagent)`.
2. **Dispatch** the subagent (read-only: concurrent; write: sequential).
3. **On return**, validate the JSON shape, then:
   - Print a one-line phase result: `Phase {n}: {passed}/{total} PASS` (or list FAIL/SKIP rows).
   - Merge `created_resources` into the state file.
   - Append `results` and update `summary` counts.
4. If a subagent returns malformed output or errors, record the phase as `FAIL` and continue (cleanup
   still runs in write mode).

---

## Placeholder Reference

The orchestrator substitutes these into each subagent's prompt (the subagent then substitutes them
into the reference-file test bodies):

| Placeholder | Source |
|---|---|
| `{checking_account_id}` | `discovery.checking_account_id` |
| `{investment_account_id}` | `discovery.investment_account_id` |
| `{test_transaction_id}` | `discovery.test_transaction_id` |
| `{valid_category_id}` | `discovery.valid_category_id` |
| `{created_tag_id}` | ID returned from the phase's most recent `create_transaction_tag` call (tracked inside the subagent) |
| `{created_txn_id}` | ID returned from the phase's most recent `create_transaction` call (tracked inside the subagent) |
| `{recurring_merchant_id}` | `merchant_id` returned by `find_merchant_id_by_name` in Phase 14.1 (tracked inside the subagent) |
| `{recurring_merchant_name}` | `merchant_name` returned by `find_merchant_id_by_name` in Phase 14.1 (tracked inside the subagent) |
