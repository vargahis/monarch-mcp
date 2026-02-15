"""Phase 3: Transaction read / query tests (14 tests)."""
# pylint: disable=missing-function-docstring

import json


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


async def test_basic_limit(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap(
        [_make_txn(i) for i in range(10)]
    )

    result = json.loads(
        (await mcp_client.call_tool("get_transactions", {"limit": 10})).content[0].text
    )

    assert len(result) == 10
    mock_monarch_client.get_transactions.assert_called_once_with(limit=10, offset=0)


# ---------------------------------------------------------------------------
# 3.2 – date range filtering
# ---------------------------------------------------------------------------


async def test_date_range(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([_make_txn(0)])

    await mcp_client.call_tool(
        "get_transactions", {"start_date": "2025-01-01", "end_date": "2025-01-31"}
    )

    mock_monarch_client.get_transactions.assert_called_once_with(
        limit=100,
        offset=0,
        start_date="2025-01-01",
        end_date="2025-01-31",
    )


# ---------------------------------------------------------------------------
# 3.3 – account_id filtering
# ---------------------------------------------------------------------------


async def test_account_id_filter(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([_make_txn(0)])

    await mcp_client.call_tool("get_transactions", {"account_id": "acc-1"})

    mock_monarch_client.get_transactions.assert_called_once_with(
        limit=100, offset=0, account_ids=["acc-1"]
    )


# ---------------------------------------------------------------------------
# 3.4 – combined account + date
# ---------------------------------------------------------------------------


async def test_combined_account_and_date(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([_make_txn(0)])

    await mcp_client.call_tool(
        "get_transactions",
        {"start_date": "2025-01-01", "end_date": "2025-01-31", "account_id": "acc-1"},
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


async def test_only_start_date_error(mcp_client):
    result = json.loads(
        (await mcp_client.call_tool("get_transactions", {"start_date": "2025-01-01"})).content[0].text
    )
    assert "error" in result


# ---------------------------------------------------------------------------
# 3.6 – only end_date -> error JSON
# ---------------------------------------------------------------------------


async def test_only_end_date_error(mcp_client):
    result = json.loads(
        (await mcp_client.call_tool("get_transactions", {"end_date": "2025-01-31"})).content[0].text
    )
    assert "error" in result


# ---------------------------------------------------------------------------
# 3.7 – pagination (two calls, no overlap)
# ---------------------------------------------------------------------------


async def test_pagination_no_overlap(mcp_client, mock_monarch_client):
    page1 = [_make_txn(i) for i in range(5)]
    page2 = [_make_txn(i + 5) for i in range(5)]
    mock_monarch_client.get_transactions.side_effect = [_wrap(page1), _wrap(page2)]

    r1 = json.loads(
        (await mcp_client.call_tool("get_transactions", {"limit": 5, "offset": 0})).content[0].text
    )
    r2 = json.loads(
        (await mcp_client.call_tool("get_transactions", {"limit": 5, "offset": 5})).content[0].text
    )

    ids1 = {t["id"] for t in r1}
    ids2 = {t["id"] for t in r2}
    assert len(ids1 & ids2) == 0, "Pages must not overlap"


# ---------------------------------------------------------------------------
# 3.8 – large offset -> empty list
# ---------------------------------------------------------------------------


async def test_large_offset_empty(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([])

    result = json.loads(
        (await mcp_client.call_tool("get_transactions", {"limit": 10, "offset": 99999})).content[0].text
    )

    assert result == []


# ---------------------------------------------------------------------------
# 3.9 – limit=0
# ---------------------------------------------------------------------------


async def test_limit_zero(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([])

    result = json.loads(
        (await mcp_client.call_tool("get_transactions", {"limit": 0})).content[0].text
    )

    assert result == []
    mock_monarch_client.get_transactions.assert_called_once_with(limit=0, offset=0)


# ---------------------------------------------------------------------------
# 3.10 – negative limit
# ---------------------------------------------------------------------------


async def test_negative_limit(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([])

    result = json.loads(
        (await mcp_client.call_tool("get_transactions", {"limit": -1})).content[0].text
    )

    assert isinstance(result, list)
    mock_monarch_client.get_transactions.assert_called_once_with(limit=-1, offset=0)


# ---------------------------------------------------------------------------
# 3.11 – negative offset
# ---------------------------------------------------------------------------


async def test_negative_offset(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([])

    result = json.loads(
        (await mcp_client.call_tool("get_transactions", {"limit": 10, "offset": -1})).content[0].text
    )

    assert isinstance(result, list)
    mock_monarch_client.get_transactions.assert_called_once_with(limit=10, offset=-1)


# ---------------------------------------------------------------------------
# 3.12 – very large limit
# ---------------------------------------------------------------------------


async def test_very_large_limit(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap(
        [_make_txn(i) for i in range(3)]
    )

    result = json.loads(
        (await mcp_client.call_tool("get_transactions", {"limit": 999999})).content[0].text
    )

    assert len(result) == 3
    mock_monarch_client.get_transactions.assert_called_once_with(
        limit=999999, offset=0
    )


# ---------------------------------------------------------------------------
# 3.13 – invalid date format -> API error passthrough
# ---------------------------------------------------------------------------


async def test_invalid_date_format(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.side_effect = Exception("Invalid date format")

    result = (await mcp_client.call_tool(
        "get_transactions", {"start_date": "not-a-date", "end_date": "also-not"}
    )).content[0].text

    assert "Error" in result
    assert "Invalid date format" in result


# ---------------------------------------------------------------------------
# 3.14 – future dates -> empty list
# ---------------------------------------------------------------------------


async def test_future_dates_empty(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([])

    result = json.loads(
        (await mcp_client.call_tool(
            "get_transactions", {"start_date": "2099-01-01", "end_date": "2099-12-31"}
        )).content[0].text
    )

    assert result == []


# ---------------------------------------------------------------------------
# 3.15 – search filter
# ---------------------------------------------------------------------------


async def test_search_filter(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([_make_txn(0)])

    await mcp_client.call_tool("get_transactions", {"search": "coffee"})

    mock_monarch_client.get_transactions.assert_called_once_with(
        limit=100, offset=0, search="coffee"
    )


# ---------------------------------------------------------------------------
# 3.16 – category_ids filter
# ---------------------------------------------------------------------------


async def test_category_ids_filter(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([_make_txn(0)])

    await mcp_client.call_tool(
        "get_transactions", {"category_ids": ["cat-1", "cat-2"]}
    )

    mock_monarch_client.get_transactions.assert_called_once_with(
        limit=100, offset=0, category_ids=["cat-1", "cat-2"]
    )


# ---------------------------------------------------------------------------
# 3.17 – account_ids list filter
# ---------------------------------------------------------------------------


async def test_account_ids_filter(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([_make_txn(0)])

    await mcp_client.call_tool(
        "get_transactions", {"account_ids": ["acc-1", "acc-2"]}
    )

    mock_monarch_client.get_transactions.assert_called_once_with(
        limit=100, offset=0, account_ids=["acc-1", "acc-2"]
    )


# ---------------------------------------------------------------------------
# 3.18 – account_id + account_ids conflict -> error
# ---------------------------------------------------------------------------


async def test_account_id_and_account_ids_conflict(mcp_client):
    result = json.loads(
        (await mcp_client.call_tool(
            "get_transactions", {"account_id": "acc-1", "account_ids": ["acc-2"]}
        )).content[0].text
    )
    assert "error" in result


# ---------------------------------------------------------------------------
# 3.19 – tag_ids filter
# ---------------------------------------------------------------------------


async def test_tag_ids_filter(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([_make_txn(0)])

    await mcp_client.call_tool("get_transactions", {"tag_ids": ["tag-1"]})

    mock_monarch_client.get_transactions.assert_called_once_with(
        limit=100, offset=0, tag_ids=["tag-1"]
    )


# ---------------------------------------------------------------------------
# 3.20 – boolean filters
# ---------------------------------------------------------------------------


async def test_bool_filters(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([_make_txn(0)])

    await mcp_client.call_tool(
        "get_transactions", {"has_notes": True, "is_recurring": False}
    )

    mock_monarch_client.get_transactions.assert_called_once_with(
        limit=100, offset=0, has_notes=True, is_recurring=False
    )


# ---------------------------------------------------------------------------
# 3.21 – hidden_from_reports filter
# ---------------------------------------------------------------------------


async def test_hidden_from_reports_filter(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([_make_txn(0)])

    await mcp_client.call_tool(
        "get_transactions", {"hidden_from_reports": True}
    )

    mock_monarch_client.get_transactions.assert_called_once_with(
        limit=100, offset=0, hidden_from_reports=True
    )


# ---------------------------------------------------------------------------
# 3.22 – combined search and filters
# ---------------------------------------------------------------------------


async def test_combined_search_and_filters(mcp_client, mock_monarch_client):
    mock_monarch_client.get_transactions.return_value = _wrap([_make_txn(0)])

    await mcp_client.call_tool(
        "get_transactions",
        {
            "search": "grocery",
            "category_ids": ["cat-1"],
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "is_split": False,
        },
    )

    mock_monarch_client.get_transactions.assert_called_once_with(
        limit=100,
        offset=0,
        start_date="2025-01-01",
        end_date="2025-01-31",
        search="grocery",
        category_ids=["cat-1"],
        is_split=False,
    )
