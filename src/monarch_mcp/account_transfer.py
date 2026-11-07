"""
GraphQL operations and helpers for Monarch's "Transfer account data" tool.

These mirror the operations the Monarch web app uses for its Transfer Data
wizard (moving transaction and balance history from an old/duplicate account
to a new one). The server performs the move itself: it deletes overlapping
data on the destination on/before the cutover date, moves the source data,
and optionally hides the source account. There is no server-side undo.
"""

from typing import Any, Dict, List, Optional

from gql import gql

ELIGIBILITY_QUERY = gql(
    """
    query Common_AccountsTransferEligibility($accountIds: [UUID!]!) {
        accountsTransferEligibility(accountIds: $accountIds) {
            canTransfer
            reason
        }
    }
    """
)

ACCOUNTS_FOR_TRANSFER_QUERY = gql(
    """
    query Web_GetAccountsForTransfer($fromAccountId: UUID!, $toAccountId: UUID!) {
        fromAccount: account(id: $fromAccountId) {
            id
            displayName
            mask
            createdAt
            dataProvider
            isHidden
            currentBalance
            syncDisabled
        }
        toAccount: account(id: $toAccountId) {
            id
            displayName
            mask
            createdAt
            dataProvider
            isHidden
            currentBalance
            syncDisabled
        }
    }
    """
)

RECOMMENDED_DATES_QUERY = gql(
    """
    query Web_RecommendedAccountDataTransferDates($fromAccountId: ID, $toAccountId: ID) {
        recommendedAccountDataTransferDates(
            fromAccountId: $fromAccountId
            toAccountId: $toAccountId
        ) {
            transactionsStartDate
            transactionsEndDate
            snapshotsStartDate
            snapshotsEndDate
        }
    }
    """
)

_WINDOW_TRANSACTION_FIELDS = """
    transactionsInWindow {
        id
        date
        amount
        pending
        plaidName
        notes
        merchant { name }
        category { name }
    }
"""

PREVIEW_TRANSACTIONS_QUERY = gql(
    """
    query Web_PreviewAccountDataTransferTransactions(
        $input: PreviewAccountDataTransferTransactionsInput!
    ) {
        previewAccountDataTransferTransactions(input: $input) {
            fromAccountSummary {
                %(window)s
                numTransactionsOlderThanWindow
                numTransactionsNewerThanWindow
                numTransactions
                numOlderTransactions
                numNewerTransactions
            }
            toAccountSummary {
                %(window)s
                numTransactionsOlderThanWindow
                numTransactionsNewerThanWindow
                numTransactions
                numOlderTransactions
                numNewerTransactions
            }
        }
    }
    """
    % {"window": _WINDOW_TRANSACTION_FIELDS}
)

PREVIEW_SNAPSHOTS_QUERY = gql(
    """
    query Web_PreviewAccountDataTransferSnapshots($input: PreviewCopySnapshotsInput!) {
        previewAccountDataTransferSnapshots(input: $input) {
            previewSnapshots {
                date
                signedBalance
            }
            fromAccountSummary {
                numSnapshots
            }
            toAccountSummary {
                numSnapshots
                numNewerSnapshots
            }
        }
    }
    """
)

TRANSFER_STATUS_QUERY = gql(
    """
    query Common_AccountTransferStatusQuery($fromAccountId: ID!) {
        accountTransferStatus(fromAccountId: $fromAccountId) {
            inProgress
        }
    }
    """
)

TRANSFER_RESULT_QUERY = gql(
    """
    query Common_AccountTransferResultQuery($transferRequestId: String!) {
        accountTransferResult(transferRequestId: $transferRequestId) {
            success
            error
            numTransactionsAffected
            numBalanceSnapshotsAffected
        }
    }
    """
)

TRANSFER_MUTATION = gql(
    """
    mutation Common_TransferAccountDataAsync($input: TransferAccountDataMutationInput!) {
        transferAccountDataAsync(input: $input) {
            transferRequestId
            errors {
                code
                message
            }
        }
    }
    """
)


async def fetch_eligibility(client, account_ids: List[str]) -> Any:
    """Return Monarch's transfer eligibility for the given account IDs."""
    result = await client.gql_call(
        operation="Common_AccountsTransferEligibility",
        graphql_query=ELIGIBILITY_QUERY,
        variables={"accountIds": account_ids},
    )
    return result.get("accountsTransferEligibility")


async def fetch_transfer_status(client, from_account_id: str) -> Optional[Dict[str, Any]]:
    """Return whether a transfer from ``from_account_id`` is currently running."""
    result = await client.gql_call(
        operation="Common_AccountTransferStatusQuery",
        graphql_query=TRANSFER_STATUS_QUERY,
        variables={"fromAccountId": from_account_id},
    )
    return result.get("accountTransferStatus")


async def fetch_transfer_result(client, transfer_request_id: str) -> Optional[Dict[str, Any]]:
    """Return the outcome of an async transfer request (None while running)."""
    result = await client.gql_call(
        operation="Common_AccountTransferResultQuery",
        graphql_query=TRANSFER_RESULT_QUERY,
        variables={"transferRequestId": transfer_request_id},
    )
    return result.get("accountTransferResult")


def _summarize_window(summary: Optional[Dict[str, Any]], include_window: bool) -> Dict[str, Any]:
    summary = dict(summary or {})
    window = summary.pop("transactionsInWindow", None) or []
    if include_window:
        summary["transactionsInWindow"] = window
    else:
        summary["transactionsInWindowCount"] = len(window)
    return summary


def _required_count(summary: Any, field: str, description: str) -> int:
    """Reject incomplete previews rather than treating missing counts as zero."""
    count = summary.get(field) if isinstance(summary, dict) else None
    if type(count) is not int or count < 0:  # pylint: disable=unidiomatic-typecheck
        raise RuntimeError(f"Monarch returned no valid {description} count")
    return count


async def build_transfer_preview(  # pylint: disable=too-many-arguments,too-many-locals
    client,
    *,
    from_account_id: str,
    to_account_id: str,
    transfer_transactions: bool = True,
    transactions_start_date: Optional[str] = None,
    transactions_end_date: Optional[str] = None,
    transfer_balances: bool = True,
    balances_start_date: Optional[str] = None,
    balances_end_date: Optional[str] = None,
    include_window_transactions: bool = False,
    include_preview_snapshots: bool = False,
) -> Dict[str, Any]:
    """Assemble the same preview the web wizard shows before a transfer.

    Unspecified dates default to Monarch's recommended dates. The returned
    ``transfer_input`` / ``expected_counts`` are exactly what
    :func:`execute_transfer` needs, so a caller can review then commit.
    """
    accounts = await client.gql_call(
        operation="Web_GetAccountsForTransfer",
        graphql_query=ACCOUNTS_FOR_TRANSFER_QUERY,
        variables={"fromAccountId": from_account_id, "toAccountId": to_account_id},
    )
    recommended_raw = await client.gql_call(
        operation="Web_RecommendedAccountDataTransferDates",
        graphql_query=RECOMMENDED_DATES_QUERY,
        variables={"fromAccountId": from_account_id, "toAccountId": to_account_id},
    )
    recommended = recommended_raw.get("recommendedAccountDataTransferDates") or {}
    eligibility = await fetch_eligibility(client, [from_account_id, to_account_id])

    warnings: List[str] = []
    expected = {
        "from_account_transaction_count": 0,
        "to_account_transaction_count": 0,
        "balance_snapshot_count": 0,
        "to_account_balance_snapshot_count": 0,
    }

    tx_start = transactions_start_date or recommended.get("transactionsStartDate")
    tx_end = transactions_end_date or recommended.get("transactionsEndDate")
    tx_preview = None
    if transfer_transactions:
        if not tx_start or not tx_end:
            warnings.append(
                "No transactions to move (no recommended transaction dates); "
                "transfer_transactions forced to false."
            )
            transfer_transactions = False
        else:
            raw = await client.gql_call(
                operation="Web_PreviewAccountDataTransferTransactions",
                graphql_query=PREVIEW_TRANSACTIONS_QUERY,
                variables={
                    "input": {
                        "fromAccountId": from_account_id,
                        "toAccountId": to_account_id,
                        "startDate": tx_start,
                        "endDate": tx_end,
                        "previewDays": 2,
                    }
                },
            )
            data = raw.get("previewAccountDataTransferTransactions")
            if not isinstance(data, dict):
                raise RuntimeError("Monarch returned no transaction transfer preview")
            from_data = data.get("fromAccountSummary")
            to_data = data.get("toAccountSummary")
            expected["from_account_transaction_count"] = _required_count(
                from_data, "numTransactions", "source transaction"
            )
            expected["to_account_transaction_count"] = _required_count(
                to_data, "numTransactions", "destination transaction"
            )
            from_summary = _summarize_window(
                from_data, include_window_transactions
            )
            to_summary = _summarize_window(
                to_data, include_window_transactions
            )
            tx_preview = {"fromAccountSummary": from_summary, "toAccountSummary": to_summary}

    bal_start = balances_start_date or recommended.get("snapshotsStartDate")
    bal_end = balances_end_date or recommended.get("snapshotsEndDate")
    bal_preview = None
    if transfer_balances:
        if not bal_start or not bal_end:
            warnings.append(
                "No balances to move (no recommended snapshot dates); "
                "transfer_balances forced to false."
            )
            transfer_balances = False
        else:
            raw = await client.gql_call(
                operation="Web_PreviewAccountDataTransferSnapshots",
                graphql_query=PREVIEW_SNAPSHOTS_QUERY,
                variables={
                    "input": {
                        "fromAccountId": from_account_id,
                        "toAccountId": to_account_id,
                        "cutoverDate": None,
                        "startDate": bal_start,
                        "endDate": bal_end,
                    }
                },
            )
            snapshot_data = raw.get("previewAccountDataTransferSnapshots")
            if not isinstance(snapshot_data, dict):
                raise RuntimeError("Monarch returned no balance transfer preview")
            expected["balance_snapshot_count"] = _required_count(
                snapshot_data.get("fromAccountSummary"), "numSnapshots", "source balance"
            )
            expected["to_account_balance_snapshot_count"] = _required_count(
                snapshot_data.get("toAccountSummary"), "numSnapshots", "destination balance"
            )
            data = dict(snapshot_data)
            snapshots = data.pop("previewSnapshots", None) or []
            if include_preview_snapshots:
                data["previewSnapshots"] = snapshots
            else:
                data["previewSnapshotCount"] = len(snapshots)
            bal_preview = data

    if eligibility and isinstance(eligibility, dict) and not eligibility.get("canTransfer"):
        warnings.append(f"Monarch reports transfer not allowed: {eligibility.get('reason')}")

    return {
        "from_account": accounts.get("fromAccount"),
        "to_account": accounts.get("toAccount"),
        "eligibility": eligibility,
        "recommended_dates": recommended,
        "transactions_preview": tx_preview,
        "balances_preview": bal_preview,
        "transfer_input": {
            "from_account_id": from_account_id,
            "to_account_id": to_account_id,
            "transfer_transactions": transfer_transactions,
            "transactions_start_date": tx_start if transfer_transactions else None,
            "transactions_end_date": tx_end if transfer_transactions else None,
            "transfer_balances": transfer_balances,
            "balances_start_date": bal_start if transfer_balances else None,
            "balances_end_date": bal_end if transfer_balances else None,
        },
        "expected_counts": expected,
        "warnings": warnings,
    }


def build_mutation_input(
    transfer_input: Dict[str, Any],
    expected_counts: Dict[str, int],
    cleanup_from_account: bool,
) -> Dict[str, Any]:
    """Map a preview's ``transfer_input`` to ``TransferAccountDataMutationInput``."""
    variables: Dict[str, Any] = {
        "fromAccountId": transfer_input["from_account_id"],
        "toAccountId": transfer_input["to_account_id"],
        "transferTransactions": bool(transfer_input["transfer_transactions"]),
        "fromAccountExpectedAffectedTransactionCount": expected_counts[
            "from_account_transaction_count"
        ],
        "toAccountExpectedAffectedTransactionCount": expected_counts[
            "to_account_transaction_count"
        ],
        "transferBalanceSnapshots": bool(transfer_input["transfer_balances"]),
        "expectedAffectedBalanceSnapshotCount": expected_counts["balance_snapshot_count"],
        "cleanupFromAccount": cleanup_from_account,
    }
    # The web app omits unset dates rather than sending null.
    for key, gql_key in (
        ("transactions_start_date", "startDateTransactions"),
        ("transactions_end_date", "endDateTransactions"),
        ("balances_start_date", "startDateBalanceSnapshots"),
        ("balances_end_date", "endDateBalanceSnapshots"),
    ):
        if transfer_input.get(key):
            variables[gql_key] = transfer_input[key]
    return variables


async def execute_transfer(client, mutation_input: Dict[str, Any]) -> Dict[str, Any]:
    """Start the async transfer and return ``transferRequestId`` / ``errors``."""
    result = await client.gql_call(
        operation="Common_TransferAccountDataAsync",
        graphql_query=TRANSFER_MUTATION,
        variables={"input": mutation_input},
    )
    return result.get("transferAccountDataAsync") or {}
