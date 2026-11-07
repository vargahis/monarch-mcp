"""Tests for the account data transfer and balance-history upload tools."""
# pylint: disable=missing-function-docstring,redefined-outer-name

import json
from unittest.mock import patch

import pytest
from gql.transport.exceptions import TransportServerError

FROM_ID = "acct-old"
TO_ID = "acct-new"

RESPONSES = {
    "Web_GetAccountsForTransfer": {
        "fromAccount": {"id": FROM_ID, "displayName": "Old"},
        "toAccount": {"id": TO_ID, "displayName": "New"},
    },
    "Web_RecommendedAccountDataTransferDates": {
        "recommendedAccountDataTransferDates": {
            "transactionsStartDate": "2013-01-02",
            "transactionsEndDate": "2026-08-27",
            "snapshotsStartDate": "2023-12-01",
            "snapshotsEndDate": "2026-11-06",
        }
    },
    "Common_AccountsTransferEligibility": {
        "accountsTransferEligibility": {"canTransfer": True, "reason": None}
    },
    "Web_PreviewAccountDataTransferTransactions": {
        "previewAccountDataTransferTransactions": {
            "fromAccountSummary": {
                "transactionsInWindow": [{"id": "t1"}, {"id": "t2"}],
                "numTransactions": 572,
                "numNewerTransactions": 0,
            },
            "toAccountSummary": {
                "transactionsInWindow": [{"id": "t3"}],
                "numTransactions": 330,
                "numNewerTransactions": 12,
            },
        }
    },
    "Web_PreviewAccountDataTransferSnapshots": {
        "previewAccountDataTransferSnapshots": {
            "previewSnapshots": [{"date": "2026-11-06", "signedBalance": 10.0}],
            "fromAccountSummary": {"numSnapshots": 1063},
            "toAccountSummary": {"numSnapshots": 1, "numNewerSnapshots": 1},
        }
    },
    "Common_AccountTransferStatusQuery": {"accountTransferStatus": {"inProgress": False}},
    "Common_TransferAccountDataAsync": {
        "transferAccountDataAsync": {"transferRequestId": "req-1", "errors": None}
    },
    "Common_AccountTransferResultQuery": {
        "accountTransferResult": {
            "success": True,
            "error": None,
            "numTransactionsAffected": 902,
            "numBalanceSnapshotsAffected": 1063,
        }
    },
}

EXPECTED = {
    "expected_from_transaction_count": 572,
    "expected_to_transaction_count": 330,
    "expected_balance_snapshot_count": 1063,
    "expected_to_balance_snapshot_count": 1,
}

DATES = {
    "transactions_start_date": "2013-01-02",
    "transactions_end_date": "2026-08-27",
    "balances_start_date": "2023-12-01",
    "balances_end_date": "2026-11-06",
}


@pytest.fixture
def gql_responses(mock_monarch_client):
    responses = json.loads(json.dumps(RESPONSES))

    async def _gql_call(operation, graphql_query, variables):  # pylint: disable=unused-argument
        return responses[operation]

    mock_monarch_client.gql_call.side_effect = _gql_call
    return responses


def _ops(mock_client):
    return [c.kwargs["operation"] for c in mock_client.gql_call.call_args_list]


def _call_vars(mock_client, operation):
    for c in mock_client.gql_call.call_args_list:
        if c.kwargs["operation"] == operation:
            return c.kwargs["variables"]
    raise AssertionError(f"{operation} not called")


async def test_preview_uses_recommended_dates(  # pylint: disable=unused-argument
    mcp_client, mock_monarch_client, gql_responses,
):
    result = json.loads(
        (await mcp_client.call_tool(
            "preview_account_data_transfer",
            {"from_account_id": FROM_ID, "to_account_id": TO_ID},
        )).content[0].text
    )

    assert result["expected_counts"] == {
        "from_account_transaction_count": 572,
        "to_account_transaction_count": 330,
        "balance_snapshot_count": 1063,
        "to_account_balance_snapshot_count": 1,
    }
    assert result["transfer_input"]["transactions_end_date"] == "2026-08-27"
    assert result["transfer_input"]["balances_end_date"] == "2026-11-06"
    assert result["transactions_preview"]["fromAccountSummary"]["transactionsInWindowCount"] == 2
    assert "Web_TransferAccountDataAsync" not in _ops(mock_monarch_client)
    assert "Common_TransferAccountDataAsync" not in _ops(mock_monarch_client)
    tx_input = _call_vars(
        mock_monarch_client, "Web_PreviewAccountDataTransferTransactions"
    )["input"]
    assert tx_input == {
        "fromAccountId": FROM_ID,
        "toAccountId": TO_ID,
        "startDate": "2013-01-02",
        "endDate": "2026-08-27",
        "previewDays": 2,
    }


async def test_preview_disables_type_without_recommended_dates(
    mcp_client, mock_monarch_client, gql_responses,
):
    gql_responses["Web_RecommendedAccountDataTransferDates"] = {
        "recommendedAccountDataTransferDates": {
            "transactionsStartDate": None,
            "transactionsEndDate": None,
            "snapshotsStartDate": "2023-12-01",
            "snapshotsEndDate": "2026-11-06",
        }
    }

    result = json.loads(
        (await mcp_client.call_tool(
            "preview_account_data_transfer",
            {"from_account_id": FROM_ID, "to_account_id": TO_ID},
        )).content[0].text
    )

    assert result["transfer_input"]["transfer_transactions"] is False
    assert result["warnings"]
    assert "Web_PreviewAccountDataTransferTransactions" not in _ops(mock_monarch_client)


async def test_transfer_executes_with_matching_counts(
    mcp_write_client, mock_monarch_client, gql_responses,  # pylint: disable=unused-argument
):
    with patch("monarch_mcp.server.asyncio.sleep"):
        result = json.loads(
            (await mcp_write_client.call_tool(
                "transfer_account_data",
                {"from_account_id": FROM_ID, "to_account_id": TO_ID, **EXPECTED, **DATES},
            )).content[0].text
        )

    assert result["started"] is True
    assert result["result"]["success"] is True
    assert _call_vars(mock_monarch_client, "Common_TransferAccountDataAsync")["input"] == {
        "fromAccountId": FROM_ID,
        "toAccountId": TO_ID,
        "transferTransactions": True,
        "startDateTransactions": "2013-01-02",
        "endDateTransactions": "2026-08-27",
        "fromAccountExpectedAffectedTransactionCount": 572,
        "toAccountExpectedAffectedTransactionCount": 330,
        "transferBalanceSnapshots": True,
        "startDateBalanceSnapshots": "2023-12-01",
        "endDateBalanceSnapshots": "2026-11-06",
        "expectedAffectedBalanceSnapshotCount": 1063,
        "cleanupFromAccount": True,
    }


async def test_transfer_aborts_when_counts_drift(
    mcp_write_client, mock_monarch_client, gql_responses,  # pylint: disable=unused-argument
):
    result = json.loads(
        (await mcp_write_client.call_tool(
            "transfer_account_data",
            {
                "from_account_id": FROM_ID,
                "to_account_id": TO_ID,
                **EXPECTED,
                **DATES,
                "expected_to_transaction_count": 329,
            },
        )).content[0].text
    )

    assert result["started"] is False
    assert result["current_counts"]["to_account_transaction_count"] == 330
    assert "Common_TransferAccountDataAsync" not in _ops(mock_monarch_client)


async def test_transfer_aborts_when_ineligible(
    mcp_write_client, mock_monarch_client, gql_responses,
):
    gql_responses["Common_AccountsTransferEligibility"] = {
        "accountsTransferEligibility": {"canTransfer": False, "reason": "same account"}
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "transfer_account_data",
            {"from_account_id": FROM_ID, "to_account_id": TO_ID, **EXPECTED, **DATES},
        )).content[0].text
    )

    assert result["started"] is False
    assert "Common_TransferAccountDataAsync" not in _ops(mock_monarch_client)


async def test_transfer_aborts_when_in_progress(
    mcp_write_client, mock_monarch_client, gql_responses,
):
    gql_responses["Common_AccountTransferStatusQuery"] = {
        "accountTransferStatus": {"inProgress": True}
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "transfer_account_data",
            {"from_account_id": FROM_ID, "to_account_id": TO_ID, **EXPECTED, **DATES},
        )).content[0].text
    )

    assert result["started"] is False
    assert _ops(mock_monarch_client) == ["Common_AccountTransferStatusQuery"]


async def test_balance_only_transfer_omits_transaction_dates(
    mcp_write_client, mock_monarch_client, gql_responses,  # pylint: disable=unused-argument
):
    with patch("monarch_mcp.server.asyncio.sleep"):
        await mcp_write_client.call_tool(
            "transfer_account_data",
            {
                "from_account_id": FROM_ID,
                "to_account_id": TO_ID,
                "transfer_transactions": False,
                "expected_from_transaction_count": 0,
                "expected_to_transaction_count": 0,
                "expected_balance_snapshot_count": 1063,
                "expected_to_balance_snapshot_count": 1,
                "balances_start_date": DATES["balances_start_date"],
                "balances_end_date": DATES["balances_end_date"],
                "cleanup_from_account": False,
            },
        )

    sent = _call_vars(mock_monarch_client, "Common_TransferAccountDataAsync")["input"]
    assert sent["transferTransactions"] is False
    assert "startDateTransactions" not in sent
    assert sent["cleanupFromAccount"] is False


async def test_transfer_requires_reviewed_dates(mcp_write_client, mock_monarch_client):
    result = (await mcp_write_client.call_tool(
        "transfer_account_data",
        {"from_account_id": FROM_ID, "to_account_id": TO_ID, **EXPECTED},
    )).content[0].text

    assert "dates from the reviewed preview" in result
    mock_monarch_client.gql_call.assert_not_called()


async def test_transfer_requires_the_requested_accounts(
    mcp_write_client, mock_monarch_client, gql_responses,
):
    gql_responses["Web_GetAccountsForTransfer"]["toAccount"] = None

    result = json.loads((await mcp_write_client.call_tool(
        "transfer_account_data",
        {"from_account_id": FROM_ID, "to_account_id": TO_ID, **EXPECTED, **DATES},
    )).content[0].text)

    assert result["started"] is False
    assert "Common_TransferAccountDataAsync" not in _ops(mock_monarch_client)


@pytest.mark.parametrize(
    ("operation", "field"),
    [
        ("Common_AccountTransferStatusQuery", "accountTransferStatus"),
        ("Common_AccountsTransferEligibility", "accountsTransferEligibility"),
    ],
)
async def test_transfer_fails_closed_for_unknown_status_or_eligibility(
    mcp_write_client, mock_monarch_client, gql_responses, operation, field,
):
    gql_responses[operation][field] = None

    result = json.loads((await mcp_write_client.call_tool(
        "transfer_account_data",
        {"from_account_id": FROM_ID, "to_account_id": TO_ID, **EXPECTED, **DATES},
    )).content[0].text)

    assert result["started"] is False
    assert "Common_TransferAccountDataAsync" not in _ops(mock_monarch_client)


@pytest.mark.parametrize(
    ("operation", "preview", "summary", "count"),
    [
        ("Web_PreviewAccountDataTransferTransactions", "previewAccountDataTransferTransactions",
         "fromAccountSummary", "numTransactions"),
        ("Web_PreviewAccountDataTransferTransactions", "previewAccountDataTransferTransactions",
         "toAccountSummary", "numTransactions"),
        ("Web_PreviewAccountDataTransferSnapshots", "previewAccountDataTransferSnapshots",
         "fromAccountSummary", "numSnapshots"),
        ("Web_PreviewAccountDataTransferSnapshots", "previewAccountDataTransferSnapshots",
         "toAccountSummary", "numSnapshots"),
    ],
)
async def test_transfer_rejects_missing_preview_counts(
    mcp_write_client, mock_monarch_client, gql_responses, operation, preview, summary, count,
):
    del gql_responses[operation][preview][summary][count]

    result = (await mcp_write_client.call_tool(
        "transfer_account_data",
        {"from_account_id": FROM_ID, "to_account_id": TO_ID, **EXPECTED, **DATES},
    )).content[0].text

    assert "no valid" in result
    assert "Common_TransferAccountDataAsync" not in _ops(mock_monarch_client)


async def test_transfer_aborts_when_destination_balance_count_drifts(
    mcp_write_client, mock_monarch_client, gql_responses,  # pylint: disable=unused-argument
):
    result = json.loads((await mcp_write_client.call_tool(
        "transfer_account_data",
        {
            "from_account_id": FROM_ID,
            "to_account_id": TO_ID,
            **EXPECTED,
            **DATES,
            "expected_to_balance_snapshot_count": 0,
        },
    )).content[0].text)

    assert result["started"] is False
    assert result["current_counts"]["to_account_balance_snapshot_count"] == 1
    assert "Common_TransferAccountDataAsync" not in _ops(mock_monarch_client)


async def test_transfer_without_request_id_reports_unknown_outcome(
    mcp_write_client, mock_monarch_client, gql_responses,
):
    gql_responses["Common_TransferAccountDataAsync"]["transferAccountDataAsync"] = {
        "transferRequestId": None,
        "errors": None,
    }

    result = (await mcp_write_client.call_tool(
        "transfer_account_data",
        {"from_account_id": FROM_ID, "to_account_id": TO_ID, **EXPECTED, **DATES},
    )).content[0].text

    assert "outcome is unknown" in result
    assert _ops(mock_monarch_client).count("Common_TransferAccountDataAsync") == 1


async def test_transfer_keeps_request_id_when_polling_fails(
    mcp_write_client, mock_monarch_client, gql_responses,  # pylint: disable=unused-argument
):
    with (
        patch("monarch_mcp.server.asyncio.sleep"),
        patch(
            "monarch_mcp.server.account_transfer.fetch_transfer_result",
            side_effect=TransportServerError("Unavailable", code=503),
        ),
    ):
        result = json.loads((await mcp_write_client.call_tool(
            "transfer_account_data",
            {"from_account_id": FROM_ID, "to_account_id": TO_ID, **EXPECTED, **DATES},
        )).content[0].text)

    assert result["transfer_request_id"] == "req-1"
    assert result["result"] is None
    assert "before retrying" in result["note"]


async def test_upload_balance_history(mcp_write_client, mock_monarch_client):
    mock_monarch_client.upload_account_balance_history.return_value = True

    result = json.loads(
        (await mcp_write_client.call_tool(
            "upload_account_balance_history",
            {
                "account_id": TO_ID,
                "balances": [
                    {"date": "2026-09-01", "amount": 100.5},
                    {"date": "2026-09-02", "amount": "99"},
                ],
            },
        )).content[0].text
    )

    assert result == {"account_id": TO_ID, "rows": 2, "completed": True}
    args = mock_monarch_client.upload_account_balance_history.call_args
    rows = args.args[1]
    assert [r.date.strftime("%Y-%m-%d") for r in rows] == ["2026-09-01", "2026-09-02"]
    assert [r.amount for r in rows] == [100.5, 99.0]


async def test_upload_balance_history_rejects_bad_rows(mcp_write_client, mock_monarch_client):
    result = (await mcp_write_client.call_tool(
        "upload_account_balance_history",
        {"account_id": TO_ID, "balances": [{"date": "09/01/2026", "amount": 1}]},
    )).content[0].text

    assert "Invalid balance row" in result
    mock_monarch_client.upload_account_balance_history.assert_not_called()
