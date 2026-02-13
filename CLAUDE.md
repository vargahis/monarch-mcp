# CLAUDE.md — Monarch MCP Server

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
py -m pylint src/monarch_mcp_server/
```
Must score **10.00/10**. There is no pylint config file; the project uses pylint defaults.

## Test Coverage — Update on Feature Changes

When new MCP tool functionality is added or existing tools are updated, **both** of the following must be updated:

1. **Unit tests** in `tests/` — pytest, mocked via `conftest.py` fixtures
2. **Integration skill** at `.claude/skills/test-monarch-mcp/` — update `SKILL.md` and reference files in `references/`
