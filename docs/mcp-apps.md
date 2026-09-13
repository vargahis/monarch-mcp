# MCP Apps for the Monarch MCP Server — capability review and proposal

Status: **proposal / investigation notes** (no implementation yet).
Researched against MCP Apps spec revision `2026-01-26` (SEP-1865, extension
`io.modelcontextprotocol/ui`).

---

## 1. What this server exposes today

| Surface | Count | Notes |
|---|---|---|
| Tools | 44 | 27 read, 17 write (write tools are `enabled=_WRITE_ENABLED`) |
| Resources | 0 | none registered |
| Prompts | 0 | none registered |
| Completions / sampling / elicitation | 0 | unused |

Every tool returns `str` — almost always `json.dumps(..., indent=2)`. Consequences:

- **No `structuredContent`.** A tool that returns a `dict` (or a Pydantic model)
  makes FastMCP emit `structuredContent` *in addition to* the text block. Today
  every payload is a pre-serialised string, so there is no machine-readable
  channel a UI could bind to.
- **Payloads are large and model-facing.** `get_budgets`, `get_cashflow`,
  `get_account_holdings`, `get_aggregate_snapshots` and
  `get_recurring_transactions` pass the raw Monarch payload straight through
  with `indent=2`. Every byte lands in the model's context, even when the user
  only wanted to *look* at it. `get_transactions` is the one tool that already
  trims fields and drops indentation — evidence that payload size is a known
  pain point.
- **Multi-step edits cost one round trip each.** Triaging 40 `needs_review`
  transactions is 40 `update_transaction` calls, each one a model turn with the
  full tool result echoed back.

These three properties are exactly what MCP Apps addresses.

## 2. How MCP Apps works (the parts that matter here)

1. The **host/client** advertises support in `initialize`:
   `capabilities.extensions["io.modelcontextprotocol/ui"] = {"mimeTypes": ["text/html;profile=mcp-app"]}`.
   The server does **not** have to negotiate anything — it only has to offer the
   right resource and metadata.
2. The server registers a self-contained HTML document as a resource with a
   `ui://` URI and mimeType `text/html;profile=mcp-app`.
3. A tool points at it via `_meta.ui.resourceUri`. Optional sibling fields:
   `visibility` (`["model"]`, `["app"]`, default both), `csp`
   (`connectDomains`, `resourceDomains`, `frameDomains`, `baseUriDomains`),
   `permissions` (clipboard/camera/mic/geolocation), `prefersBorder`.
4. On a tool call the host renders the HTML in a sandboxed iframe and pushes
   data in over JSON-RPC: `ui/notifications/tool-input` then
   `ui/notifications/tool-result` (carrying `content`, `structuredContent`,
   `isError`).
5. The iframe can call back: `tools/call` and `tools/list` (host-mediated and
   host-validated), plus `ui/open-link`, `ui/download-file`, `ui/message`,
   `ui/request-display-mode`, `ui/update-model-context`, and
   `ui/notifications/size-changed`. `ui/notifications/host-context-changed`
   delivers theme/locale/dimension changes.
6. Hosts that don't support the extension ignore the metadata and show the
   normal text result — adding a UI never breaks an existing client, **provided
   the text content stays meaningful**.

### Feasibility on our current pin — verified

`pyproject.toml` pins `fastmcp>=2.12.0,<3.0.0` (lock: 2.14.5, `mcp` 1.30.0).
There is no `mcp.server.apps` module and no FastMCP apps helper at that version,
**but nothing is blocked** — the extension is metadata plus a resource, and
2.14.5 already carries every hook needed. Probed directly against 2.14.5:

- `@mcp.resource("ui://…", mime_type="text/html;profile=mcp-app", meta={...})`
  registers and reads back with the profile mimeType intact.
- `@mcp.tool(meta={"ui": {"resourceUri": "ui://…"}})` serialises to
  `_meta.ui.resourceUri` on `tools/list` (FastMCP adds its own `_fastmcp` key
  alongside; harmless).
- A tool returning a `dict` emits `structuredContent` *and* a compact JSON text
  block. `output_schema=None` suppresses the output schema without losing
  `structuredContent`.
- Host capabilities are reachable from inside a tool for graceful degradation:
  `get_context().session.client_params.capabilities` — `ClientCapabilities` has
  `extra="allow"`, so the unknown `extensions` key survives validation and the
  server can detect an app-capable host.

FastMCP 3.x / `mcp` SDK 2.x add first-class sugar (`Apps()`,
`apps.add_html_resource(...)`, `client_supports_apps(ctx)`, auto mimeType for
`ui://`). Nice to have; not a prerequisite. Lifting the `<3.0.0` pin should be a
separate decision.

## 3. Where MCP Apps pays off here — ranked

### Tier 1 — build these first

**1. Transaction review queue** (`get_transactions(needs_review=True)` + app-only
`update_transaction` / `set_transaction_tags`)
A table with a category picker, tag chips, notes field and split shortcut per
row. The user triages 40 transactions with 40 clicks instead of 40 model turns,
then the app calls `ui/update-model-context` once with a summary ("12
recategorised, 3 tagged Business") so the conversation can continue informed.
This is the single largest ergonomic win available and the best showcase for
`visibility: ["app"]`: the mutating tools are reachable by the user's click but
not by the model.

**2. Budget dashboard with inline editing** (`get_budgets` + `set_budget_amount`)
`get_budgets` is the heaviest read in the server and the least readable as JSON.
Render progress bars per category group (spent / budgeted / remaining, over-budget
highlighted), with an editable amount field writing back through
`set_budget_amount` (`apply_to_future` as a checkbox — a flag users routinely get
wrong when it is buried in a tool call). Pair it with a short text summary for
the model: "7 of 31 categories over budget; $412 net over." Context cost drops by
an order of magnitude while the user gets *more* detail, not less.

**3. Cashflow & net-worth charts** (`get_cashflow`, `get_cashflow_summary`,
`get_aggregate_snapshots`, `get_account_snapshots_by_type`, `get_credit_history`)
All five are time series or category breakdowns that currently arrive as raw
JSON. One generic `ui://monarch/chart.html` (inline SVG, no external library) can
serve several of them via `structuredContent`, keyed by a `chart` field in the
payload: monthly income/expense bars, net-worth line, category treemap or
horizontal bars, credit-score sparkline.

### Tier 2 — high value, narrower

**4. Transaction rule builder** (`get_transaction_rules`, `create_transaction_rule`,
`update_transaction_rule`)
`CreateTransactionRuleInput` is the most complex input in the server (nested
criteria + actions, Monarch's REPLACE semantics on update). A form that composes
the criteria and shows a live **"matches N of your last 200 transactions"**
preview — by calling `get_transactions(search=...)` from the app before
committing — turns a blind write into a reviewed one. The rules list gets
readable cards with the application stats the tool already returns.

**5. Split editor** (`get_transaction_splits` + `update_transaction_splits`)
Splits must sum to the parent amount. Arithmetic the UI can enforce live
(remainder indicator, "split evenly", percentage mode) instead of failing
server-side after a model miscalculation.

**6. Recurring bills calendar** (`get_recurring_transactions` +
`update_recurring_merchant`)
A month grid of upcoming bills with totals per week. Clicking a bill edits
frequency/amount — and the widget can encode the rule that `is_recurring` is
mandatory on every call (the constraint that previously produced Monarch's opaque
"Something went wrong").

**7. Accounts / net-worth panel** (`get_accounts`, `get_institutions`,
`refresh_accounts`)
Accounts grouped by type with balances, institution sync state, and a Refresh
button. Worth pairing with `is_accounts_refresh_complete` from
[MISSING_FEATURES.md](../MISSING_FEATURES.md) so the button can show real progress
rather than fire-and-forget.

### Tier 3 — do carefully, or not at all

**8. Connection health panel** (`check_auth_status`, `get_institutions`,
`get_subscription_details`)
Keyring state, session age, per-institution connection errors, and a
"Re-authenticate" button that uses `ui/open-link` to open the existing
local auth page.

**Explicit non-goal: never collect Monarch credentials or MFA codes in an app
iframe.** The server's stated security invariant is that credentials are entered
in the browser only, never through the MCP client. An iframe is rendered *by the
client*, and anything typed there travels over host-mediated JSON-RPC. The app
may *trigger* the browser flow; it must not replace it.

## 4. Cross-cutting engineering notes

- **Structured output is the real prerequisite.** Give app-backed tools a `dict`
  return (or a parallel `*_app` variant) so the UI binds to `structuredContent`
  while the model-facing text stays a short summary. Returning `dict` changes the
  wire shape for existing clients (adds `outputSchema` + `structuredContent`);
  `output_schema=None` keeps the schema off if that matters.
- **`visibility` is the interesting lever.** `["app"]` on mutating tools means
  the user can act by clicking while the model cannot call them at all — a real
  safety upgrade for a finance server, and complementary to the existing
  read-only/write-mode split. Note that enforcement is the *host's*; FastMCP
  still lists the tool.
- **Read-only mode interaction.** Write tools don't exist in the tool list in
  read-only mode, so every widget must discover its capabilities via `tools/list`
  and render read-only when the write tools are absent — not assume and fail.
- **Self-contained HTML.** No CDN: external loads require declaring
  `csp.resourceDomains` / `connectDomains`. Inline the CSS and JS, hand-roll
  charts as inline SVG, and honour the host theme via
  `ui/notifications/host-context-changed`.
- **Packaging.** Keep widgets as real files (e.g. `src/monarch_mcp/ui/*.html`),
  not string literals in `server.py` — that file is already 1628 lines with
  `too-many-lines` disabled. `.mcpb` bundles `src/` already; a pip/uvx install
  needs `[tool.setuptools.package-data]` (`monarch_mcp = ["ui/*.html"]`), which
  is currently absent.
- **Cache-bust by URI.** Hosts may cache a `ui://` resource by URI; version it
  (`ui://monarch/budget@2.html`) when the markup changes materially.
- **Degrade loudly in text.** Keep returning a useful text summary in `content`
  so non-app hosts (and the model itself) lose nothing.

## 5. Testing, per CLAUDE.md's three surfaces

- **Mocked unit tests** (the gate): resource registered at the expected `ui://`
  URI with mimeType `text/html;profile=mcp-app`; tool `_meta.ui.resourceUri`
  matches a registered resource; `structuredContent` shape per app-backed tool;
  text fallback still present and compact. All deterministic — the right home by
  the routing rule.
- **Live integration tests**: unchanged in scope — they cover tool robustness
  against the real API, and apps add no new live paths beyond the tools
  themselves.
- **Agent skill**: an agent cannot click a widget. Keep its job to "calls the
  right tool with the right params"; assert the app metadata exists rather than
  trying to test the UI. Real UI verification needs a host harness (the ext-apps
  basic-host, MCPJam, or the MCP Inspector), which is a manual/dev-loop step.

## 6. Risks

- **Host rendering is not guaranteed yet.** Claude, VS Code, Goose, Postman and
  MCPJam are reported to render MCP Apps, but there is at least one open, unanswered
  ext-apps issue (#671) where a correctly negotiating server renders only the
  text fallback in Claude Desktop / claude.ai. Prototype *one* widget end to end
  in the actual target host before building a suite.
- **Spec is young.** Revision `2026-01-26` is the first final cut of the first
  MCP extension; field names (`_meta.ui.*`) and the `ui/*` method set may still
  move. Keep the metadata in one small module so a rename is a one-file change.
- **Maintenance surface.** Each widget is HTML/CSS/JS in a Python project with a
  10.00/10 pylint gate and no JS toolchain. Start with two widgets, not seven.

## 7. Suggested sequencing

1. **Spike**: one `ui://` resource + one tool (`get_budgets` → dashboard,
   read-only), verified in a real host. Proves the plumbing and the rendering
   risk in one step.
2. **Budget dashboard** with `set_budget_amount` write-back behind `tools/list`
   discovery.
3. **Review queue** with app-only write tools.
4. **Chart widget** reused across the cashflow / net-worth / credit tools.
5. Re-evaluate the FastMCP `<3.0.0` pin once two widgets exist and the
   boilerplate is visible.
