# CLAUDE.md — Monarch MCP Server

## Branching Policy

**Never commit directly to `main`** unless the user explicitly asks for it.

- If on `main`, create a new feature branch before committing (e.g., `feature/<topic>`), or switch to an existing branch.
- If unsure which branch to use, ask the user.
- This applies to all commits — fixes, features, refactors, docs, etc.

## Documentation Maintenance

Keep `README.md` up to date whenever:
- New functionality is added
- Existing functionality changes
- Installation instructions change
- The authentication process changes

## Quality Gates — Run After Every Change

Run both checks after every code change. Both must pass before committing.

```powershell
py -m pytest tests/
```
All tests must pass.

```powershell
py -m pylint src/monarch_mcp/
```
Must score **10.00/10**. There is no pylint config file; the project uses pylint defaults.

## Test Coverage — Update on Feature Changes

When new MCP tool functionality is added or existing tools are updated, update the relevant test surfaces below. There are **three**, each with a distinct job:

1. **Mocked unit tests** in `tests/` — pytest, mocked via `conftest.py` fixtures. The quality gate; runs in CI. Home for deterministic validation logic (required-field checks, mutual-exclusion, regex/format validation).
2. **Live e2e integration tests** in `tests/integration/` — pytest against a **real** Monarch account, opt-in via `MONARCH_LIVE_TESTS=1` (deselected by default, never in CI). Home for **tool robustness** against the live API: adversarial/edge inputs and live error paths (invalid ids, server-side rejections). Self-cleaning (`MCP-Test-` prefix).
3. **Agent test skill** at `.claude/skills/test-monarch-mcp/` — drives an AI agent to verify it *calls* the tools correctly (right tool, right params, correct response interpretation). Keep it to happy paths, agent-judgment cases, and one representative graceful-error case per tool family. Update `SKILL.md` (including test counts) and the `references/` files.

**Routing rule:** agent-judgment → skill; tool robustness / live-API error paths → `tests/integration/`; deterministic validation → mocked unit tests.

## No Absolute Paths

Never use absolute filesystem paths in any project file — skills, prompts, documents, source code, or configuration. Use relative paths (from the project root) or descriptive references like "the project root" instead. Generic example paths in documentation (e.g., `/path/to/venv/...`) are acceptable.
