# Monarch Money MCP Server

A Model Context Protocol (MCP) server for integrating with the Monarch Money personal finance platform through Claude Desktop.

## Overview

**Two ways to install:**

| | Claude Desktop Extension | Python Library (pip) |
|---|---|---|
| **Install** | Download `.mcpb`, add in Settings | `pip install` + JSON config |
| **Best for** | Most users | Custom setups, virtual envs |

**Two operating modes:**

The server starts in **read-only mode** by default. Write tools are hidden and blocked until you explicitly opt in.

| | Read-only (default) | Write mode |
|---|---|---|
| **View** accounts, transactions, budgets | Yes | Yes |
| **Analyze** cashflow, spending, net worth | Yes | Yes |
| **Create** transactions, tags, categories | No | Yes |
| **Update** accounts, budgets, splits | No | Yes |
| **Delete** transactions, tags, accounts | No | Yes |

## Getting Started

### Installation

#### Claude Desktop Extension (.mcpb)

1. Download the latest `.mcpb` file from [Releases](https://github.com/vargahis/monarch-mcp/releases)
2. In Claude Desktop: **Settings > Extensions > Advanced Settings > Install Extensions** (in the "Extension Developer" section) — select the downloaded `.mcpb` file
3. Restart Claude Desktop — done!

To enable write tools: **Settings > Extensions > Monarch Money MCP Server > Configure** — toggle **"Enable write tools"** and click **Save**.

#### Python Library (pip)

```bash
pip install monarch-mcp
```

> **Contributors**: See [docs/releasing.md](docs/releasing.md) for the release process, version scheme, and pre-release testing via TestPyPI.

Add this to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "Monarch Money": {
      "command": "python3",
      "args": ["-m", "monarch_mcp"]
    }
  }
}
```

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "Monarch Money": {
      "command": "py",
      "args": ["-m", "monarch_mcp"]
    }
  }
}
```

> **Note**: The `"command"` value must be whatever launches Python on your system.
> Common values: `python3` (macOS/Linux), `py` (Windows), or `python`.
> If you installed into a virtual environment, use the full path to that environment's
> interpreter instead (e.g., `/path/to/venv/bin/python3` or `C:\path\to\venv\Scripts\python.exe`).

To enable write tools, add `--enable-write` to the `args` array:

```json
{
  "mcpServers": {
    "Monarch Money": {
      "command": "python3",
      "args": ["-m", "monarch_mcp", "--enable-write"]
    }
  }
}
```

After saving the config, **restart Claude Desktop**.

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
| `get_transactions` | Get transactions with filtering | read |
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
