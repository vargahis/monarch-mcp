# Live e2e integration tests

These tests exercise the MCP **tools** against a **real** Monarch Money account to verify they behave
robustly against the live API — adversarial/edge inputs (unicode, oversized strings, extreme
pagination, huge amounts) and live error paths (invalid ids, server-side rejections).

They are distinct from:

- **`tests/` (mocked unit tests)** — the offline quality gate; never hit the network.
- **the `test-monarch-mcp` agent skill** — checks that an *AI agent* calls the tools correctly.

## Running

These tests are **deselected by default** (`addopts = -m 'not integration'` in `pyproject.toml`), so
the normal gate `uv run pytest tests/` never runs them. Run them explicitly:

```bash
MONARCH_LIVE_TESTS=1 uv run pytest tests/integration -m integration
```

The `-m integration` overrides the default deselection. Without `MONARCH_LIVE_TESTS=1` (and a
credential source) every test **skips** — double safety against accidental live runs.

### Credentials

The suite obtains a real client the same way the server does, in priority order:

1. A **keyring token** — run `python login_setup.py` once to store one. (Recommended.)
2. `MONARCH_EMAIL` / `MONARCH_PASSWORD` environment variables (the suite logs in once per session).

If neither is available, the suite skips with an explanatory message.

## Safety

- **Self-cleaning.** Every test deletes the resource it creates in a `finally`. A session-scoped
  `_final_sweep` backstop deletes any leftover `MCP-Test-`-prefixed tag / category / account /
  transaction / rule after the suite, even if a test crashed.
- **No mutation of your real data.** Update/stress cases create a throwaway `MCP-Test-` transaction,
  mutate that, and delete it — they never edit your existing transactions, so there is nothing to
  revert.
- **Your session is protected.** The fixtures neuter `secure_session.delete_token` and
  `trigger_auth_flow` for the duration of the run, so a live `401`/`403`/WAF response can never wipe
  your keyring token or pop a browser login. Worst case is `MCP-Test-` residue, which the next run
  sweeps.

## Conventions

- All created resources are prefixed with `MCP-Test-` (rules are lowercased by Monarch, so they read
  as `mcp-test`).
- Tests are **deterministic**: fixed dates, discovery of "first checking account / first category",
  and assertions only on values the test set — never on counts of your real data.
- Tests assert the MCP layer is **graceful**: a call returns either a valid JSON payload or a clean
  `Error <op>: ...` string, never an unhandled exception / traceback.

## Layout

| File | Covers |
|---|---|
| `conftest.py` | live fixtures, `_isolate` override, guardrails, `_final_sweep` |
| `test_transactions_live.py` | create/update robustness, invalid date, pagination edges |
| `test_tags_live.py` | create happy + adversarial names |
| `test_categories_live.py` | create happy + invalid group |
| `test_accounts_live.py` | create/update/delete lifecycle + invalid id |
| `test_rules_live.py` | create/list/delete lifecycle + invalid id |
| `test_error_paths_live.py` | cross-tool invalid-id graceful-error matrix |
