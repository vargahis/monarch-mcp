# Phase 9 — Transaction Details & Splits (8 tests)

> **Read-only mode:** Run tests 9.1-9.5 only. Skip 9.6-9.8 (update_transaction_splits and create_transaction require write mode).

## 9.1 — get_transaction_details: happy path
Call `get_transaction_details(transaction_id={test_transaction_id})`.
**Expected:** JSON with detailed transaction info including `id`, `date`, `amount`, `merchant`, `category`.

## 9.2 — get_transaction_details: redirect_posted=False
Call `get_transaction_details(transaction_id={test_transaction_id}, redirect_posted=False)`.
**Expected:** Success. Returns transaction details.

## 9.3 — get_transaction_details: invalid ID
Call `get_transaction_details(transaction_id="invalid-txn-id")`.
**Expected:** Error response.

## 9.4 — get_transaction_splits: no splits
Call `get_transaction_splits(transaction_id={test_transaction_id})`.
**Expected:** JSON response. The `splitTransactions` list is likely empty for the test transaction.

## 9.5 — get_transaction_splits: invalid ID
Call `get_transaction_splits(transaction_id="invalid-txn-id")`.
**Expected:** Error response.

## 9.6 — update_transaction_splits: create splits on test transaction
First, create a temporary transaction for split testing:
Call `create_transaction(account_id={checking_account_id}, amount=-100.0, merchant_name="MCP-Test-Split-Merchant", category_id={valid_category_id}, date="2025-01-15")`.
Record the ID in `created_resources.transactions`.

Then call `update_transaction_splits(transaction_id={new_txn_id}, split_data=[{"merchantName": "Part A", "amount": -60.0, "categoryId": "{valid_category_id}"}, {"merchantName": "Part B", "amount": -40.0, "categoryId": "{valid_category_id}"}])`.
**Expected:** Success.

## 9.7 — get_transaction_splits: verify splits exist
Call `get_transaction_splits(transaction_id={new_txn_id from 9.6})`.
**Expected:** Response contains 2 split transactions.

## 9.8 — update_transaction_splits: remove all splits
Call `update_transaction_splits(transaction_id={new_txn_id from 9.6}, split_data=[])`.
**Expected:** Success. Splits are removed.
