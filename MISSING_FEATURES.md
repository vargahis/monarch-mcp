# Missing Features in Monarch MCP Server

This document lists all features from the `monarchmoney` Python library that are **NOT** exposed in the MCP server, or are only partially exposed with missing parameters.

## Summary Statistics

- **Total monarchmoney methods**: 48
- **MCP tools exposed**: 14 (includes 3 helper tools not from library)
- **Library methods exposed**: 11
- **Missing library methods**: 37
- **Partially exposed (missing parameters)**: 4

---

## 1. COMPLETELY MISSING METHODS

### Authentication & Session Management (3 methods)
❌ **`interactive_login()`**
- Interactive login for iPython environments

❌ **`save_session(filename: Optional[str] = None)`**
- Save session to file manually

❌ **`load_session(filename: Optional[str] = None)`**
- Load session from file manually

**Note**: `login()`, `multi_factor_authenticate()`, and `delete_session()` are used internally by the MCP server but not exposed as tools.

---

### Account Management (7 methods)

❌ **`get_account_type_options()`**
- Get available account types and subtypes for creating accounts

❌ **`get_recent_account_balances(start_date: Optional[str] = None)`**
- Get daily account balances (defaults to last 31 days)

❌ **`get_account_snapshots_by_type(start_date: str, timeframe: str)`**
- Get net values by account type (timeframe: "year" or "month")

❌ **`get_aggregate_snapshots(start_date: Optional[date] = None, end_date: Optional[date] = None, account_type: Optional[str] = None)`**
- Get daily net value of all accounts with optional filtering

❌ **`get_account_history(account_id: int)`**
- Get account balance history

❌ **`create_manual_account(account_type: str, account_sub_type: str, is_in_net_worth: bool, account_name: str, account_balance: float = 0)`**
- Create a new manual account

❌ **`update_account(account_id: str, account_name, account_balance, account_type, account_sub_type, include_in_net_worth, hide_from_summary_list, hide_transactions_from_reports)`**
- Update account details (all parameters optional except account_id)

❌ **`delete_account(account_id: str)`**
- Delete an account

---

### Account Refresh (2 methods)

❌ **`is_accounts_refresh_complete(account_ids: Optional[List[str]] = None)`**
- Check if account refresh is complete

❌ **`request_accounts_refresh_and_wait(account_ids: Optional[List[str]] = None, timeout: int = 300, delay: int = 10)`**
- Request refresh and wait for completion with configurable timeout

**Note**: `refresh_accounts()` is exposed but doesn't accept `account_ids` parameter

---

### Transaction Management (9 methods)

❌ **`get_transactions_summary()`**
- Get transaction summary statistics

❌ **`get_transaction_details(transaction_id: str, redirect_posted: bool = True)`**
- Get detailed information about a specific transaction

❌ **`delete_transaction(transaction_id: str)`**
- Delete a transaction

❌ **`get_transaction_splits(transaction_id: str)`**
- Get split information for a transaction

❌ **`update_transaction_splits(transaction_id: str, split_data: List[Dict[str, Any]])`**
- Create, modify, or delete transaction splits

❌ **`get_recurring_transactions(start_date: Optional[str] = None, end_date: Optional[str] = None)`**
- Get upcoming recurring transactions

❌ **`upload_attachment(transaction_id: str, file_content: bytes, filename: str)`**
- Upload attachment to a transaction

---

### Transaction Categories (5 methods)

❌ **`get_transaction_categories()`**
- Get all transaction categories

❌ **`get_transaction_category_groups()`**
- Get category groups

❌ **`create_transaction_category(group_id: str, transaction_category_name: str, rollover_start_month, icon: str = '❓', rollover_enabled: bool = False, rollover_type: str = 'monthly')`**
- Create new category with rollover support

❌ **`delete_transaction_category(category_id: str)`**
- Delete a single category

❌ **`delete_transaction_categories(category_ids: List[str])`**
- Batch delete multiple categories

---

### Budgets & Goals (1 method)

❌ **`set_budget_amount(amount: float, category_id: Optional[str] = None, category_group_id: Optional[str] = None, timeframe: str = 'month', start_date: Optional[str] = None, apply_to_future: bool = False)`**
- Set budget amount for category or category group with future application

---

### Cashflow & Analytics (2 methods)

❌ **`get_cashflow_summary(limit: int = 100, start_date: Optional[str] = None, end_date: Optional[str] = None)`**
- Get cashflow summary (income, expenses, savings, savings rate)

❌ **`get_credit_history()`**
- Get credit history data

---

### Other Features (4 methods)

❌ **`get_institutions()`**
- Get list of financial institutions

❌ **`get_subscription_details()`**
- Get subscription information

❌ **`upload_account_balance_history(account_id: str, csv_content: List[BalanceHistoryRow], timeout: int = 300, delay: int = 10)`**
- Upload historical balance data via CSV

❌ **`gql_call(operation: str, graphql_query: DocumentNode, variables: Dict[str, Any] = {})`**
- Direct GraphQL query execution (advanced use)

---

### Configuration (2 methods)

❌ **`set_timeout(timeout_secs: int)`**
- Set request timeout

❌ **`set_token(token: str)`**
- Set authentication token directly

---

## 2. PARTIALLY EXPOSED (Missing Parameters)

### ⚠️ `get_transactions()` - **SEVERELY LIMITED**

**Exposed parameters** (5):
- `limit`, `offset`, `start_date`, `end_date`, `account_id`

**Missing parameters** (8):
- ❌ `search` - Search text in transactions
- ❌ `category_ids` - Filter by categories (list)
- ❌ `tag_ids` - Filter by tags (list)
- ❌ `has_attachments` - Filter transactions with attachments
- ❌ `has_notes` - Filter transactions with notes
- ❌ `hidden_from_reports` - Filter hidden transactions
- ❌ `is_split` - Filter split transactions
- ❌ `is_recurring` - Filter recurring transactions
- ❌ `imported_from_mint` - Filter Mint imports
- ❌ `synced_from_institution` - Filter synced transactions

**Impact**: Users cannot filter transactions by multiple key criteria

---

### ⚠️ `create_transaction()` - Missing Parameters

**Exposed parameters** (6):
- `account_id`, `amount`, `description`, `date`, `category_id`, `merchant_name`

**Missing parameters** (2):
- ❌ `notes` - Transaction notes
- ❌ `update_balance` - Update account balance when creating transaction

**Library signature**:
```python
create_transaction(date: str, account_id: str, amount: float,
                   merchant_name: str, category_id: str,
                   notes: str = '', update_balance: bool = False)
```

---

### ⚠️ `refresh_accounts()` - Missing Parameters

**Exposed parameters**: None (takes no parameters)

**Missing parameters** (1):
- ❌ `account_ids` - List of specific account IDs to refresh

**Library signature**:
```python
request_accounts_refresh(account_ids: List[str]) -> bool
```

**Impact**: Cannot selectively refresh specific accounts

---

### ⚠️ `get_budgets()` - Missing Parameters

**Exposed parameters**: None (takes no parameters)

**Missing parameters** (4):
- ❌ `start_date` - Budget start date filter
- ❌ `end_date` - Budget end date filter
- ❌ `use_legacy_goals` - Use legacy goals format
- ❌ `use_v2_goals` - Use v2 goals format

**Library signature**:
```python
get_budgets(start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            use_legacy_goals: Optional[bool] = False,
            use_v2_goals: Optional[bool] = True)
```

---

## 3. PRIORITY RECOMMENDATIONS

### High Priority (Most Useful)

1. **`get_transaction_categories()`** - Essential for users to see available categories
2. **`get_transaction_category_groups()`** - Essential for category organization
3. **`get_transactions()` - Add filtering parameters** - Especially `search`, `category_ids`, `tag_ids`
4. **`delete_transaction()`** - Basic CRUD operation
5. **`get_transaction_details()`** - Deep dive into specific transactions
6. **`get_transaction_splits()`** - View split transaction details
7. **`update_transaction_splits()`** - Modify split transactions
8. **`set_budget_amount()`** - Set and adjust budgets
9. **`get_recent_account_balances()`** - Track balance trends
10. **`get_cashflow_summary()`** - High-level financial overview

### Medium Priority

11. **`create_manual_account()`** - Create accounts programmatically
12. **`update_account()`** - Modify account settings
13. **`delete_account()`** - Remove accounts
14. **`get_recurring_transactions()`** - View upcoming bills
15. **`get_aggregate_snapshots()`** - Net worth tracking
16. **`create_transaction_category()`** - Custom categories
17. **`get_account_type_options()`** - Discover account types
18. **`is_accounts_refresh_complete()`** - Check refresh status
19. **`request_accounts_refresh_and_wait()`** - Blocking refresh

### Lower Priority

20. **`get_institutions()`** - List available institutions
21. **`get_subscription_details()`** - View subscription info
22. **`upload_attachment()`** - Attach files to transactions
23. **`get_credit_history()`** - Credit score tracking
24. **`upload_account_balance_history()`** - Bulk historical data
25. **`save_session()` / `load_session()`** - Manual session management
26. **`set_timeout()`** - Configure timeouts
27. **`gql_call()`** - Advanced GraphQL queries

---

## 4. PARAMETER COVERAGE MATRIX

| Feature | MCP Exposed? | Full Parameters? | Coverage % |
|---------|--------------|------------------|------------|
| `get_accounts()` | ✅ Yes | ✅ Yes | 100% |
| `get_transactions()` | ✅ Yes | ❌ No | 38% (5/13 params) |
| `get_budgets()` | ✅ Yes | ❌ No | 0% (0/4 params) |
| `get_cashflow()` | ✅ Yes | ✅ Yes | 100% |
| `get_account_holdings()` | ✅ Yes | ✅ Yes | 100% |
| `create_transaction()` | ✅ Yes | ❌ No | 75% (6/8 params) |
| `update_transaction()` | ✅ Yes | ✅ Yes | 100% |
| `refresh_accounts()` | ✅ Yes | ❌ No | 0% (0/1 params) |
| `get_transaction_tags()` | ✅ Yes | ✅ Yes | 100% |
| `create_transaction_tag()` | ✅ Yes | ✅ Yes | 100% |
| `set_transaction_tags()` | ✅ Yes | ✅ Yes | 100% |

**Overall Library Coverage**: **23%** (11/48 methods exposed)

---

## 5. IMPACT ANALYSIS

### Critical Gaps

1. **No category management** - Cannot view, create, or delete categories
2. **Limited transaction filtering** - Cannot search or filter by tags/categories
3. **No transaction splits** - Cannot work with split transactions
4. **No account CRUD** - Cannot create, update, or delete accounts
5. **No budget setting** - Can only view budgets, not set them
6. **No recurring transactions** - Cannot view upcoming bills

### Workarounds Required

Users must currently use the Monarch Money web/mobile app for:
- Viewing available categories
- Creating custom categories
- Setting budget amounts
- Managing split transactions
- Creating/deleting accounts
- Filtering transactions by multiple criteria
- Viewing recurring transaction schedules

---

## Conclusion

The MCP server currently exposes **only 23%** of the monarchmoney library's capabilities. While it covers basic read operations well, it lacks:

1. **Write operations** for categories, budgets, and accounts
2. **Advanced filtering** for transactions
3. **Split transaction support**
4. **Recurring transaction visibility**
5. **Account management** (CRUD operations)

Expanding coverage to at least the **High Priority** recommendations would significantly enhance the MCP server's utility.
