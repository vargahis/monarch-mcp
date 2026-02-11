[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/robcerda-monarch-mcp-server-badge.png)](https://mseep.ai/app/robcerda-monarch-mcp-server)

# Monarch Money MCP Server

A Model Context Protocol (MCP) server for integrating with the Monarch Money personal finance platform. This server provides seamless access to your financial accounts, transactions, budgets, and analytics through Claude Desktop.

My MonarchMoney referral: https://www.monarchmoney.com/referral/ufmn0r83yf?r_source=share

**Built with the [monarchmoneycommunity Python library](https://pypi.org/project/monarchmoneycommunity/)** - A community-maintained fork of the MonarchMoney API that provides long-lived authentication tokens and full MFA support.

> **Why this fork?** The original [hammem/monarchmoney](https://github.com/hammem/monarchmoney) library hardcodes `trusted_device: False`, resulting in 1-hour token expiration and frequent re-authentication. The monarchmoneycommunity fork (based on [bradleyseanf's work](https://github.com/bradleyseanf/monarchmoney)) sets `trusted_device: True` for long-lived tokens that last weeks/months, providing a much better user experience.

<a href="https://glama.ai/mcp/servers/@robcerda/monarch-mcp-server">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@robcerda/monarch-mcp-server/badge" alt="monarch-mcp-server MCP server" />
</a>

## 🚀 Quick Start

### 1. Installation

1. **Clone this repository**:
   ```bash
   git clone https://github.com/robcerda/monarch-mcp-server.git
   cd monarch-mcp-server
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Configure Claude Desktop**:
   Add this to your Claude Desktop configuration file:
   
   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   
   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   
   ```json
   {
     "mcpServers": {
       "Monarch Money": {
         "command": "/opt/homebrew/bin/uv",
         "args": [
           "run",
           "--with",
           "mcp[cli]",
           "--with-editable",
           "/path/to/your/monarch-mcp-server",
           "mcp",
           "run",
           "/path/to/your/monarch-mcp-server/src/monarch_mcp_server/server.py"
         ]
       }
     }
   }
   ```
   
   **Important**: Replace `/path/to/your/monarch-mcp-server` with your actual path!

4. **Restart Claude Desktop**

### 2. Authentication

Authentication happens **automatically in your browser** the first time the MCP server starts without a saved session.

1. Start (or restart) Claude Desktop
2. The server detects that no token exists and opens a login page in your browser
3. Enter your Monarch Money email and password
4. Provide your 2FA code if you have MFA enabled
5. Once authenticated, the token is saved to your system keyring — you're all set

> **Alternative — CLI login**: You can also authenticate manually by running
> `python login_setup.py` in a terminal. This is useful in headless environments
> where a browser is not available.

### 3. Start Using in Claude Desktop

Once authenticated, use these tools directly in Claude Desktop:
- `get_accounts` - View all your financial accounts
- `get_transactions` - Recent transactions with filtering
- `get_budgets` - Budget information and spending
- `get_cashflow` - Income/expense analysis

## ✨ Features

### 📊 Account Management
- **Get Accounts**: View all linked financial accounts with balances and institution info
- **Get Account Holdings**: See securities and investments in investment accounts
- **Refresh Accounts**: Request real-time data updates from financial institutions

### 💰 Transaction Access
- **Get Transactions**: Fetch transaction data with filtering by date, account, and pagination
- **Create Transaction**: Add new transactions to accounts
- **Update Transaction**: Modify existing transactions (amount, description, category, date)
- **Tag Management**: Create, view, and apply tags to organize and categorize transactions

### 📈 Financial Analysis
- **Get Budgets**: Access budget information including spent amounts and remaining balances
- **Get Cashflow**: Analyze financial cashflow over specified date ranges with income/expense breakdowns

### 🔐 Secure Authentication
- **Auto Browser Login**: A login page opens in your browser automatically when needed
- **Automatic Re-auth**: If your session expires, the browser login is re-triggered on the next tool call
- **MFA Support**: Full support for two-factor authentication
- **Session Persistence**: Tokens are stored in the system keyring and last for weeks/months
- **Secure**: Credentials are entered in your browser, never through Claude Desktop

## 🛠️ Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `setup_authentication` | Get setup instructions | None |
| `check_auth_status` | Check authentication status | None |
| `get_accounts` | Get all financial accounts | None |
| `get_transactions` | Get transactions with filtering | `limit`, `offset`, `start_date`, `end_date`, `account_id` |
| `get_budgets` | Get budget information | None |
| `get_cashflow` | Get cashflow analysis | `start_date`, `end_date` |
| `get_account_holdings` | Get investment holdings | `account_id` |
| `create_transaction` | Create new transaction | `account_id`, `amount`, `description`, `date`, `category_id`, `merchant_name` |
| `update_transaction` | Update existing transaction | `transaction_id`, `amount`, `description`, `category_id`, `date` |
| `refresh_accounts` | Request account data refresh | None |
| `get_transaction_tags` | Get all transaction tags | None |
| `create_transaction_tag` | Create new transaction tag | `name`, `color` |
| `set_transaction_tags` | Set tags on a transaction | `transaction_id`, `tag_ids` |

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
If you see "Authentication needed" errors:
1. A login page should open automatically in your browser — complete the sign-in there
2. If the browser doesn't open, run `python login_setup.py` from a terminal as a fallback
3. Restart Claude Desktop and try using a tool like `get_accounts`

### Session Expired
Sessions last for weeks, but if expired the server handles it automatically:
1. The expired token is cleared from the keyring
2. A new browser login page is opened
3. Sign in again and retry your request

### Common Error Messages
- **"Your session has expired"**: Complete the browser login that was opened and retry
- **"Authentication needed"**: Complete the browser login or run `python login_setup.py`
- **"Invalid account ID"**: Use `get_accounts` to see valid account IDs
- **"Date format error"**: Use YYYY-MM-DD format for dates

## 🏗️ Technical Details

### Project Structure
```
monarch-mcp-server/
├── src/monarch_mcp_server/
│   ├── __init__.py
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

This MCP server is built on top of the [monarchmoneycommunity](https://pypi.org/project/monarchmoneycommunity/) Python library, a community-maintained fork that provides:

- Long-lived authentication tokens (`trusted_device: True`)
- Secure authentication with MFA support
- Comprehensive API coverage for Monarch Money
- Session management and persistence

Special thanks to:
- [@hammem](https://github.com/hammem) for creating the original [monarchmoney](https://github.com/hammem/monarchmoney) library
- [@bradleyseanf](https://github.com/bradleyseanf) for the fork that implements long-lived tokens
- The community contributors maintaining the [monarchmoneycommunity](https://pypi.org/project/monarchmoneycommunity/) package

## 📄 License

MIT License

## 🆘 Support

For issues:
1. Check authentication with `check_auth_status`
2. Try any tool — if the token is missing or expired the browser login will open automatically
3. As a fallback, run `python login_setup.py` from a terminal
4. Check error logs for detailed messages
5. Ensure Monarch Money service is accessible

## 🔄 Updates

To update the server:
1. Pull latest changes from repository
2. Restart Claude Desktop
3. If needed, re-authentication will happen automatically via the browser