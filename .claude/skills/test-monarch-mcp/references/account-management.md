# Phase 11 — Account Management (10 tests)

> **Read-only mode:** Run tests 11.1, 11.6-alt, 11.7-11.10. Skip 11.2-11.6 (create/update/delete account requires write mode).

## 11.1 — get_account_type_options: returns valid types
Call `get_account_type_options()`.
**Expected:** JSON with account type options. Record a valid `account_type` and `account_sub_type` for later use.

## 11.2 — create_manual_account: happy path
Using types from 11.1, call `create_manual_account(account_name="MCP-Test-Account", account_type={type}, account_sub_type={sub_type}, is_in_net_worth=False, account_balance=0)`.
**Expected:** Success. Record the account ID in `created_resources.accounts`.

## 11.3 — update_account: rename
Call `update_account(account_id={created_account_id}, account_name="MCP-Test-Renamed")`.
**Expected:** Success.

## 11.4 — update_account: update balance
Call `update_account(account_id={created_account_id}, account_balance=1000.0)`.
**Expected:** Success.

## 11.5 — update_account: toggle net worth
Call `update_account(account_id={created_account_id}, include_in_net_worth=True)`.
**Expected:** Success.

## 11.6 — get_account_history: for created account
Call `get_account_history(account_id={created_account_id})`.
**Expected:** JSON response (may have limited history for a brand new account).

## 11.6-alt — get_account_history: for checking account (read-only variant)

> **This test replaces 11.6 in read-only mode**, since no account is created.

Call `get_account_history(account_id={checking_account_id})`.
**Expected:** JSON with historical balance snapshots for a real account.

## 11.7 — get_recent_account_balances: no date
Call `get_recent_account_balances()`.
**Expected:** JSON with balance data.

## 11.8 — get_account_snapshots_by_type: month
Call `get_account_snapshots_by_type(start_date="2025-01-01", timeframe="month")`.
**Expected:** JSON with snapshot data.

## 11.9 — get_account_snapshots_by_type: invalid timeframe
Call `get_account_snapshots_by_type(start_date="2025-01-01", timeframe="week")`.
**Expected:** JSON with `error` key about invalid timeframe.

## 11.10 — get_aggregate_snapshots: no params
Call `get_aggregate_snapshots()`.
**Expected:** JSON with aggregate snapshot data.
