"""Phase 3: Transaction read / query tests (14 tests)."""
# pylint: disable=missing-function-docstring

import json

from monarch_mcp_server.server import get_transactions

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_txn(i, **overrides):
    """Return a minimal transaction dict as the Monarch API would."""
    txn = {
        "id": f"txn-{i}",
        "date": "2025-01-15",
        "amount": -10.0 * (i + 1),
        "plaidName": f"STORE #{i}",
        "category": {"name": "Shopping"},
        "account": {"displayName": "Checking"},
        "merchant": {"name": f"Store {i}"},
        "notes": None,
        "pending": False,
        "isRecurring": False,
        "tags": [],
    }
    txn.update(overrides)
    return txn


def _wrap(txns):
    """Wrap a list of transaction dicts in the API response envelope."""
    return {"allTransactions": {"results": txns}}


# ---------------------------------------------------------------------------
# 3.1 – basic limit
# ---------------------------------------------------------------------------


def test_basic_limit(mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap(
        [_make_txn(i) for i in range(10)]
    )

    result = json.loads(get_transactions(limit=10))

    assert len(result) == 10
    mock_monarch_client.get_transactions.assert_called_once_with(limit=10, offset=0)


# ---------------------------------------------------------------------------
# 3.2 – date range filtering
# ---------------------------------------------------------------------------


def test_date_range(mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([_make_txn(0)])

    get_transactions(start_date="2025-01-01", end_date="2025-01-31")

    mock_monarch_client.get_transactions.assert_called_once_with(
        limit=100,
        offset=0,
        start_date="2025-01-01",
        end_date="2025-01-31",
    )


# ---------------------------------------------------------------------------
# 3.3 – account_id filtering
# ---------------------------------------------------------------------------


def test_account_id_filter(mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([_make_txn(0)])

    get_transactions(account_id="acc-1")

    mock_monarch_client.get_transactions.assert_called_once_with(
        limit=100, offset=0, account_ids=["acc-1"]
    )


# ---------------------------------------------------------------------------
# 3.4 – combined account + date
# ---------------------------------------------------------------------------


def test_combined_account_and_date(mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([_make_txn(0)])

    get_transactions(
        start_date="2025-01-01", end_date="2025-01-31", account_id="acc-1"
    )

    mock_monarch_client.get_transactions.assert_called_once_with(
        limit=100,
        offset=0,
        start_date="2025-01-01",
        end_date="2025-01-31",
        account_ids=["acc-1"],
    )


# ---------------------------------------------------------------------------
# 3.5 – only start_date -> error JSON
# ---------------------------------------------------------------------------


def test_only_start_date_error():
    result = json.loads(get_transactions(start_date="2025-01-01"))
    assert "error" in result


# ---------------------------------------------------------------------------
# 3.6 – only end_date -> error JSON
# ---------------------------------------------------------------------------


def test_only_end_date_error():
    result = json.loads(get_transactions(end_date="2025-01-31"))
    assert "error" in result


# ---------------------------------------------------------------------------
# 3.7 – pagination (two calls, no overlap)
# ---------------------------------------------------------------------------


def test_pagination_no_overlap(mock_monarch_client):
    page1 = [_make_txn(i) for i in range(5)]
    page2 = [_make_txn(i + 5) for i in range(5)]
    mock_monarch_client.get_transactions.side_effect = [_wrap(page1), _wrap(page2)]

    r1 = json.loads(get_transactions(limit=5, offset=0))
    r2 = json.loads(get_transactions(limit=5, offset=5))

    ids1 = {t["id"] for t in r1}
    ids2 = {t["id"] for t in r2}
    assert len(ids1 & ids2) == 0, "Pages must not overlap"


# ---------------------------------------------------------------------------
# 3.8 – large offset -> empty list
# ---------------------------------------------------------------------------


def test_large_offset_empty(mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([])

    result = json.loads(get_transactions(limit=10, offset=99999))

    assert result == []


# ---------------------------------------------------------------------------
# 3.9 – limit=0
# ---------------------------------------------------------------------------


def test_limit_zero(mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([])

    result = json.loads(get_transactions(limit=0))

    assert result == []
    mock_monarch_client.get_transactions.assert_called_once_with(limit=0, offset=0)


# ---------------------------------------------------------------------------
# 3.10 – negative limit
# ---------------------------------------------------------------------------


def test_negative_limit(mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([])

    result = json.loads(get_transactions(limit=-1))

    assert isinstance(result, list)
    mock_monarch_client.get_transactions.assert_called_once_with(limit=-1, offset=0)


# ---------------------------------------------------------------------------
# 3.11 – negative offset
# ---------------------------------------------------------------------------


def test_negative_offset(mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([])

    result = json.loads(get_transactions(limit=10, offset=-1))

    assert isinstance(result, list)
    mock_monarch_client.get_transactions.assert_called_once_with(limit=10, offset=-1)


# ---------------------------------------------------------------------------
# 3.12 – very large limit
# ---------------------------------------------------------------------------


def test_very_large_limit(mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap(
        [_make_txn(i) for i in range(3)]
    )

    result = json.loads(get_transactions(limit=999999))

    assert len(result) == 3
    mock_monarch_client.get_transactions.assert_called_once_with(
        limit=999999, offset=0
    )


# ---------------------------------------------------------------------------
# 3.13 – invalid date format -> API error passthrough
# ---------------------------------------------------------------------------


def test_invalid_date_format(mock_monarch_client):
    mock_monarch_client.get_transactions.side_effect = Exception("Invalid date format")

    result = get_transactions(start_date="not-a-date", end_date="also-not")

    assert "Error" in result
    assert "Invalid date format" in result


# ---------------------------------------------------------------------------
# 3.14 – future dates -> empty list
# ---------------------------------------------------------------------------


def test_future_dates_empty(mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([])

    result = json.loads(
        get_transactions(start_date="2099-01-01", end_date="2099-12-31")
    )

    assert result == []
