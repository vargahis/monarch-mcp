# Monarch Money MCP Server

A Model Context Protocol (MCP) server for integrating with the Monarch Money personal finance platform. This server provides seamless access to your financial accounts, transactions, budgets, and analytics through Claude Desktop.

**Built with the [monarchmoneycommunity Python library](https://pypi.org/project/monarchmoneycommunity/)** - A community-maintained fork of the MonarchMoney API that provides long-lived authentication tokens and full MFA support.

## 🚀 Quick Start

### Option A: One-click Install (Claude Desktop)

1. Download the latest `.mcpb` file from [Releases](https://github.com/vargahis/monarch-mcp-server/releases)
2. In Claude Desktop, click **"Install Extension..."** and select the downloaded file
3. Restart Claude Desktop — done!

### Option B: Install from TestPyPI

> **Why TestPyPI?** The package is currently in pre-release testing. Once validated, it will be published to the main Python Package Index (PyPI) and the install command will simplify to `pip install monarch-mcp-server`.

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ monarch-mcp-server
```

Then [configure Claude Desktop](#configure-claude-desktop) and restart it.

### Option C: From Source

```bash
git clone https://github.com/vargahis/monarch-mcp-server.git
cd monarch-mcp-server
pip install -r requirements.txt
pip install -e .
```

Then [configure Claude Desktop](#configure-claude-desktop) and restart it.

### Configure Claude Desktop

Add this to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "Monarch Money": {
      "command": "python3",
      "args": ["-m", "monarch_mcp_server"]
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
      "args": ["-m", "monarch_mcp_server"]
    }
  }
}
```

> **Note**: The `"command"` value must be whatever launches Python on your system.
> Common values: `python3` (macOS/Linux), `py` (Windows), or `python`.
> If you installed into a virtual environment, use the full path to that environment's
> interpreter instead (e.g., `/path/to/venv/bin/python3` or `C:\path\to\venv\Scripts\python.exe`).

After saving the config, **restart Claude Desktop**.

### Authentication

Authentication happens **automatically in your browser** the first time the MCP server starts without a saved session.

1. Start (or restart) Claude Desktop
2. The server detects that no token exists and opens a login page in your browser
3. Enter your Monarch Money email and password
4. Provide your 2FA code if you have MFA enabled
5. Once authenticated, the token is saved to your system keyring — you're all set

> **Alternative — CLI login**: You can also authenticate manually by running
> `python login_setup.py` in a terminal. This is useful in headless environments
> where a browser is not available.

### Start Using in Claude Desktop

Once authenticated, use these tools directly in Claude Desktop:
- `get_accounts` - View all your financial accounts
- `get_transactions` - Recent transactions with filtering
- `get_budgets` - Budget information and spending
- `get_cashflow` - Income/expense analysis

## ✨ Features

### 📊 Account Management
- **Get Accounts**: View all linked financial accounts with balances and institution info
- **Get Account Holdings**: See securities and investments in investment accounts
- **Create Manual Account**: Add manual accounts (property, crypto, etc.)
- **Update Account**: Modify account settings (name, balance, net worth inclusion, visibility)
- **Delete Account**: Remove an account permanently
- **Refresh Accounts**: Request real-time data updates from financial institutions
- **Get Institutions**: View connected financial institutions and their sync status
- **Account History & Snapshots**: Historical balance data, daily balances, and net worth snapshots

### 💰 Transaction Access
- **Get Transactions**: Fetch with advanced filtering — search, categories, tags, date ranges, account, boolean flags (has notes, is recurring, is split, etc.)
- **Get Transaction Details**: Full detail for a single transaction including attachments and splits
- **Create Transaction**: Add new transactions with optional balance update
- **Update Transaction**: Modify existing transactions (amount, description, category, date)
- **Transaction Splits**: View and manage split transactions
- **Tag Management**: Create, view, delete, and apply tags to organize transactions

### 📈 Financial Analysis
- **Get Budgets**: Access budget information including spent amounts and remaining balances
- **Set Budget Amount**: Set or update budget amounts for categories or category groups
- **Get Cashflow**: Analyze financial cashflow with income/expense breakdowns
- **Get Cashflow Summary**: Quick summary of income, expenses, savings, and savings rate
- **Get Transactions Summary**: Aggregate stats (count, sum, avg, max, income, expenses)
- **Get Recurring Transactions**: View subscriptions and recurring bills
- **Get Credit History**: Credit score history and trends

### 🏷️ Category Management
- **Get Categories**: View all transaction categories and their groups
- **Create Category**: Add new categories with optional rollover settings
- **Delete Category**: Remove a transaction category

### 📋 Account Info
- **Get Subscription Details**: Check Monarch Money subscription status
- **Get Account Type Options**: View available account types for manual account creation

### 🔐 Secure Authentication
- **Auto Browser Login**: A login page opens in your browser automatically when needed
- **Automatic Re-auth**: If your session expires, the browser login is re-triggered on the next tool call
- **MFA Support**: Full support for two-factor authentication
- **Session Persistence**: Tokens are stored in the system keyring and last for weeks/months
- **Secure**: Credentials are entered in your browser, never through Claude Desktop

## 🛠️ Available Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| **Auth** | | |
| `setup_authentication` | Get setup instructions | None |
| `check_auth_status` | Check authentication status | None |
| `debug_session_loading` | Debug keyring issues | None |
| **Accounts** | | |
| `get_accounts` | Get all financial accounts | None |
| `get_account_holdings` | Get investment holdings | `account_id` |
| `create_manual_account` | Create manual account | `account_name`, `account_type`, `account_sub_type`, `is_in_net_worth` |
| `update_account` | Update account settings | `account_id`, `account_name`, `account_balance`, `include_in_net_worth`, ... |
| `delete_account` | Delete an account | `account_id` |
| `refresh_accounts` | Request account data refresh | None |
| `get_institutions` | Get connected institutions | None |
| `get_account_type_options` | Get valid account types | None |
| `get_account_history` | Get historical balance data | `account_id` |
| `get_recent_account_balances` | Get daily balances | `start_date` |
| `get_account_snapshots_by_type` | Net worth by account type | `start_date`, `timeframe` |
| `get_aggregate_snapshots` | Daily aggregate net value | `start_date`, `end_date`, `account_type` |
| **Transactions** | | |
| `get_transactions` | Get transactions with filtering | `limit`, `offset`, `start_date`, `end_date`, `account_id`, `search`, `category_ids`, `tag_ids`, `is_recurring`, ... |
| `get_transaction_details` | Get full transaction detail | `transaction_id`, `redirect_posted` |
| `get_transactions_summary` | Aggregate transaction stats | None |
| `create_transaction` | Create new transaction | `account_id`, `amount`, `merchant_name`, `category_id`, `date`, `notes`, `update_balance` |
| `update_transaction` | Update existing transaction | `transaction_id`, `amount`, `merchant_name`, `category_id`, `date`, `notes`, ... |
| `delete_transaction` | Delete a transaction | `transaction_id` |
| `get_transaction_splits` | Get split information | `transaction_id` |
| `update_transaction_splits` | Create/modify/delete splits | `transaction_id`, `split_data` |
| `get_recurring_transactions` | Get recurring transactions | `start_date`, `end_date` |
| **Tags** | | |
| `get_transaction_tags` | Get all tags | None |
| `create_transaction_tag` | Create new tag | `name`, `color` |
| `delete_transaction_tag` | Delete a tag | `tag_id` |
| `set_transaction_tags` | Set tags on a transaction | `transaction_id`, `tag_ids` |
| **Categories** | | |
| `get_transaction_categories` | Get all categories | None |
| `get_transaction_category_groups` | Get category groups | None |
| `create_transaction_category` | Create a category | `group_id`, `name`, `icon`, `rollover_enabled` |
| `delete_transaction_category` | Delete a category | `category_id` |
| **Budgets & Cashflow** | | |
| `get_budgets` | Get budget information | `start_date`, `end_date`, `use_v2_goals` |
| `set_budget_amount` | Set budget for category | `amount`, `category_id` or `category_group_id`, `timeframe`, `apply_to_future` |
| `get_cashflow` | Get cashflow analysis | `start_date`, `end_date` |
| `get_cashflow_summary` | Get cashflow summary | `limit`, `start_date`, `end_date` |
| **Other** | | |
| `get_subscription_details` | Get subscription status | None |
| `get_credit_history` | Get credit score history | None |

## 📝 Usage Examples

### View Your Accounts
```
Use get_accounts to show me all my financial accounts
```

### Get Recent Transactions
```
Show me my last 50 transactions using get_transactions with limit 50
```

### Check Spending vs Budget
```
Use get_budgets to show my current budget status
```

### Analyze Cash Flow
```
Get my cashflow for the last 3 months using get_cashflow
```

### Manage Transaction Tags
```
Show me all my transaction tags using get_transaction_tags
```

```
Create a new tag called "Business Expenses" with color "#FF5733" using create_transaction_tag
```

```
Apply tags to a transaction: use set_transaction_tags with transaction_id and a list of tag_ids
```

## 📅 Date Formats

- All dates should be in `YYYY-MM-DD` format (e.g., "2024-01-15")
- Transaction amounts: **positive** for income, **negative** for expenses

## 🔧 Troubleshooting

### Authentication Issues
If you encounter authentication errors, the server will automatically open a browser login page. Complete the sign-in there and retry your request. If the browser doesn't open automatically, run `python login_setup.py` as a fallback.

### Common Error Messages
- **"Your session has expired"** / **"Authentication needed"**: Complete the browser login that opens automatically
- **"Invalid account ID"**: Use `get_accounts` to see valid account IDs
- **"Date format error"**: Use YYYY-MM-DD format for dates

## 🏗️ Technical Details

### Project Structure
```
monarch-mcp-server/
├── src/monarch_mcp_server/
│   ├── __init__.py
│   ├── __main__.py        # python -m monarch_mcp_server entry point
│   ├── server.py          # Main server implementation
│   ├── auth_server.py     # Browser-based authentication server
│   └── secure_session.py  # Keyring-based token storage
├── login_setup.py         # CLI authentication setup (fallback)
├── pyproject.toml         # Project configuration
├── requirements.txt       # Dependencies
└── README.md             # This documentation
```

### Authentication Flow
1. On startup the server checks for a token in the system keyring
2. If no token is found, a local HTTP server is started on a random port and the browser is opened to a login page
3. The user signs in (with MFA if enabled); the token is saved to the keyring
4. The temporary auth server shuts down automatically
5. If a token later expires, the same flow is re-triggered on the next tool call

### Session Management
- Tokens are stored securely in the system keyring (service: `com.mcp.monarch-mcp-server`)
- Sessions persist across Claude Desktop restarts
- Expired tokens are detected automatically and cleared

### Security Features
- Credentials are entered in your local browser, never transmitted through Claude Desktop
- The auth server binds to `127.0.0.1` only (not accessible from the network)
- MFA/2FA fully supported
- Token stored in the OS keyring, not in plain-text files

## 🙏 Acknowledgments

This repository is a fork of [robcerda/monarch-mcp-server](https://github.com/robcerda/monarch-mcp-server), maintained by vargahis.

This MCP server is built on top of the [monarchmoneycommunity](https://pypi.org/project/monarchmoneycommunity/) Python library, a community-maintained fork that provides:

- Long-lived authentication tokens (`trusted_device: True`)
- Secure authentication with MFA support
- Comprehensive API coverage for Monarch Money
- Session management and persistence

Special thanks to:
- [@robcerda](https://github.com/robcerda) for creating the original [monarch-mcp-server](https://github.com/robcerda/monarch-mcp-server)
- [@hammem](https://github.com/hammem) for creating the original [monarchmoney](https://github.com/hammem/monarchmoney) library
- [@bradleyseanf](https://github.com/bradleyseanf) for the fork that implements long-lived tokens
- The community contributors maintaining the [monarchmoneycommunity](https://pypi.org/project/monarchmoneycommunity/) package

## 📄 License

MIT License

## 🆘 Support

For issues, check authentication with `check_auth_status` or try any tool to trigger automatic browser login if needed. See the Troubleshooting section above for common errors.

## 🔄 Updates

To update the server:
1. Pull latest changes from repository
2. Restart Claude Desktop
3. If needed, re-authentication will happen automatically via the browser