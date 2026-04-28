# Monarch Money MCP Server
<!-- mcp-name: io.github.vargahis/monarch-money -->

A Model Context Protocol (MCP) server for integrating with the Monarch Money personal finance platform through Claude Desktop.

## Overview

- **Secure by design** — browser-based login, token stored in OS keychain (never in config files or env vars)
- **Safe by default** — read-only mode prevents accidental changes; write tools require explicit opt-in
- **Comprehensive** — 38 tools covering accounts, transactions, splits, budgets, cashflow, tags, categories, rules, and credit history
- **Easy to install** — Claude Desktop extension (`.mcpb`), `uvx`, or `pip`

**Two operating modes:**

The server starts in **read-only mode** by default. Write tools are hidden and blocked until you explicitly opt in.

| | Read-only (default) | Write mode |
|---|---|---|
| **View** accounts, transactions, budgets | Yes | Yes |
| **Analyze** cashflow, spending, net worth | Yes | Yes |
| **Create** transactions, tags, categories, rules | No | Yes |
| **Update** accounts, budgets, splits | No | Yes |
| **Delete** transactions, tags, accounts | No | Yes |

## Quick Start

### Installation

#### Option 1: Claude Desktop Extension (.mcpb) — Recommended for Claude Desktop

> Enables toggling write mode on/off directly from the Claude Desktop app.

1. Download the latest `.mcpb` from [Releases](https://github.com/vargahis/monarch-mcp/releases)
2. In Claude Desktop: **Settings > Extensions > Advanced Settings > Install Extensions** — select the `.mcpb` file
3. Restart Claude Desktop

To enable write tools: **Settings > Extensions > Monarch Money MCP Server > Configure** — toggle **"Enable write tools"** and click **Save**.

---

#### Option 2: uvx (no install required) — Recommended for agents (e.g. Claude Code or Cursor)

> Also works with Claude Desktop, but write mode cannot be toggled from the app — set it in the config instead.

Add to your MCP config file:

```json
{
  "mcpServers": {
    "Monarch Money": {
      "command": "uvx",
      "args": ["monarch-mcp"]
    }
  }
}
```

To enable write tools:

```json
{
  "mcpServers": {
    "Monarch Money": {
      "command": "uvx",
      "args": ["monarch-mcp", "--enable-write"]
    }
  }
}
```

---

#### Option 3: pip install — Recommended for local installation and venv

```bash
pip install monarch-mcp
```

> **Contributors**: See [docs/releasing.md](docs/releasing.md) for the release process, version scheme, and pre-release testing via TestPyPI.

Add to your MCP config using the full path to your Python interpreter:

```json
{
  "mcpServers": {
    "Monarch Money": {
      "command": "/path/to/bin/python3",
      "args": ["-m", "monarch_mcp"]
    }
  }
}
```

To enable write tools, add `"--enable-write"` to `args`.

---

#### Option 4: Clone and install — Recommended for development

```bash
git clone https://github.com/vargahis/monarch-mcp.git
cd monarch-mcp
pip install -e .
```

Then add to your MCP config using the Python interpreter from your dev environment:

```json
{
  "mcpServers": {
    "Monarch Money": {
      "command": "/path/to/bin/python3",
      "args": ["-m", "monarch_mcp"]
    }
  }
}
```

To enable write tools, add `"--enable-write"` to `args`.

### Authentication

Authentication happens **automatically in your browser** the first time the MCP server starts without a saved session.

1. Start (or restart) Claude Desktop
2. The server detects that no token exists and opens a login page in your browser
3. Enter your Monarch Money email and password
4. Provide your 2FA code if you have MFA enabled
5. Once authenticated, the token is saved to your system keyring — you're all set

Key details:

- **Credentials are entered in your browser only** — never through Claude Desktop
- **Token stored in the OS keyring** — persists across restarts, lasts weeks/months
- **Expired sessions re-authenticate automatically** — the browser login re-triggers on the next tool call
- **MFA fully supported**
- **Fallback**: run `python login_setup.py` in a terminal for headless environments

For technical details on the auth architecture, see [docs/authentication.md](docs/authentication.md).

### Usage Examples

```
Show me all my financial accounts
```

```
What were my last 50 transactions?
```

```
How's my budget looking this month?
```

```
Analyze my cashflow for the last 3 months
```

```
Create a tag called "Business Expenses" in red
```

## Available Tools

| Tool | Description | Mode |
|------|-------------|------|
| **Auth** | | |
| `setup_authentication` | Get setup instructions | read |
| `check_auth_status` | Check authentication status | read |
| `debug_session_loading` | Debug keyring issues | read |
| **Accounts** | | |
| `get_accounts` | Get all financial accounts | read |
| `get_account_holdings` | Get investment holdings | read |
| `get_account_history` | Get historical balance data | read |
| `get_recent_account_balances` | Get daily balances | read |
| `get_account_snapshots_by_type` | Net worth by account type | read |
| `get_aggregate_snapshots` | Daily aggregate net value | read |
| `get_institutions` | Get connected institutions | read |
| `get_account_type_options` | Get valid account types | read |
| `refresh_accounts` | Request account data refresh | read |
| `create_manual_account` | Create manual account | write |
| `update_account` | Update account settings | write |
| `delete_account` | Delete an account | write |
| **Transactions** | | |
| `get_transactions` | Get transactions with filtering (date, account, category, tag, search, needs\_review, and more) | read |
| `get_transaction_details` | Get full transaction detail | read |
| `get_transactions_summary` | Aggregate transaction stats | read |
| `get_transaction_splits` | Get split information | read |
| `get_recurring_transactions` | Get recurring transactions | read |
| `create_transaction` | Create new transaction | write |
| `update_transaction` | Update existing transaction | write |
| `delete_transaction` | Delete a transaction | write |
| `update_transaction_splits` | Create/modify/delete splits | write |
| **Tags** | | |
| `get_transaction_tags` | Get all tags | read |
| `create_transaction_tag` | Create new tag | write |
| `delete_transaction_tag` | Delete a tag | write |
| `set_transaction_tags` | Set tags on a transaction | write |
| **Categories** | | |
| `get_transaction_categories` | Get all categories | read |
| `get_transaction_category_groups` | Get category groups | read |
| `create_transaction_category` | Create a category | write |
| `delete_transaction_category` | Delete a category | write |
| **Rules** | | |
| `create_transaction_rule` | Create an auto-categorization rule | write |
| **Budgets & Cashflow** | | |
| `get_budgets` | Get budget information | read |
| `get_cashflow` | Get cashflow analysis | read |
| `get_cashflow_summary` | Get cashflow summary | read |
| `set_budget_amount` | Set budget for category | write |
| **Other** | | |
| `get_subscription_details` | Get subscription status | read |
| `get_credit_history` | Get credit score history | read |

## 🙏 Acknowledgments

Forked from [@robcerda](https://github.com/robcerda)'s [monarch-mcp-server](https://github.com/robcerda/monarch-mcp-server), maintained by vargahis.

Built on the [monarchmoneycommunity](https://pypi.org/project/monarchmoneycommunity/) Python library. 

Thanks to:
- [@robcerda](https://github.com/robcerda) for the original MCP server
- [@hammem](https://github.com/hammem) for the original [monarchmoney](https://github.com/hammem/monarchmoney) library
- [@bradleyseanf](https://github.com/bradleyseanf) for the community fork

## License

MIT License
