"""Phase 6: Transaction CRUD tests (25 tests)."""
# pylint: disable=missing-function-docstring

import json

from gql.transport.exceptions import TransportServerError


# ===================================================================
# Helpers
# ===================================================================


def _api_txn(**overrides):
    """Minimal API-shaped transaction response."""
    txn = {
        "id": "txn-new",
        "date": "2025-01-15",
        "amount": -42.50,
        "merchant": {"name": "Coffee Shop"},
        "category": {"name": "Food & Drink"},
    }
    txn.update(overrides)
    return txn


# ===================================================================
# CREATE (9 tests)
# ===================================================================


async def test_create_happy(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_transaction.return_value = _api_txn()

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction",
            {
                "account_id": "acc-1",
                "amount": -42.50,
                "merchant_name": "Coffee Shop",
                "category_id": "cat-1",
                "date": "2025-01-15",
                "notes": "Morning coffee",
            },
        )).content[0].text
    )

    assert result["id"] == "txn-new"
    mock_monarch_client.create_transaction.assert_called_once_with(
        date="2025-01-15",
        account_id="acc-1",
        amount=-42.50,
        merchant_name="Coffee Shop",
        category_id="cat-1",
        notes="Morning coffee",
        update_balance=False,
    )


async def test_create_positive_amount(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_transaction.return_value = _api_txn(amount=500.00)

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction",
            {
                "account_id": "acc-1",
                "amount": 500.00,
                "merchant_name": "Employer",
                "category_id": "cat-income",
                "date": "2025-01-15",
            },
        )).content[0].text
    )

    assert result["amount"] == 500.00


async def test_create_no_notes(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_transaction.return_value = _api_txn()

    await mcp_write_client.call_tool(
        "create_transaction",
        {
            "account_id": "acc-1",
            "amount": -10.0,
            "merchant_name": "Store",
            "category_id": "cat-1",
            "date": "2025-01-15",
        },
    )

    # notes defaults to "" when not provided
    call_kwargs = mock_monarch_client.create_transaction.call_args[1]
    assert call_kwargs["notes"] == ""


async def test_create_invalid_account(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_transaction.side_effect = Exception(
        "Account not found"
    )

    result = (await mcp_write_client.call_tool(
        "create_transaction",
        {
            "account_id": "bad-acc",
            "amount": -10.0,
            "merchant_name": "Store",
            "category_id": "cat-1",
            "date": "2025-01-15",
        },
    )).content[0].text

    assert "Error" in result
    assert "Account not found" in result


async def test_create_invalid_category(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_transaction.side_effect = Exception(
        "Category not found"
    )

    result = (await mcp_write_client.call_tool(
        "create_transaction",
        {
            "account_id": "acc-1",
            "amount": -10.0,
            "merchant_name": "Store",
            "category_id": "bad-cat",
            "date": "2025-01-15",
        },
    )).content[0].text

    assert "Error" in result
    assert "Category not found" in result


async def test_create_invalid_date(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_transaction.side_effect = Exception("Invalid date")

    result = (await mcp_write_client.call_tool(
        "create_transaction",
        {
            "account_id": "acc-1",
            "amount": -10.0,
            "merchant_name": "Store",
            "category_id": "cat-1",
            "date": "not-a-date",
        },
    )).content[0].text

    assert "Error" in result


async def test_create_zero_amount(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_transaction.return_value = _api_txn(amount=0.0)

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction",
            {
                "account_id": "acc-1",
                "amount": 0.0,
                "merchant_name": "Adjustment",
                "category_id": "cat-1",
                "date": "2025-01-15",
            },
        )).content[0].text
    )

    assert result["amount"] == 0.0


async def test_create_large_amount(mcp_write_client, mock_monarch_client):
    big = 9999999.99
    mock_monarch_client.create_transaction.return_value = _api_txn(amount=big)

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction",
            {
                "account_id": "acc-1",
                "amount": big,
                "merchant_name": "Mega Corp",
                "category_id": "cat-1",
                "date": "2025-01-15",
            },
        )).content[0].text
    )

    assert result["amount"] == big


async def test_create_unicode_merchant(mcp_write_client, mock_monarch_client):
    name = "\u5496\u5561\u5e97 \u2615"
    mock_monarch_client.create_transaction.return_value = _api_txn(
        merchant={"name": name}
    )

    result = json.loads(
        (await mcp_write_client.call_tool(
            "create_transaction",
            {
                "account_id": "acc-1",
                "amount": -5.0,
                "merchant_name": name,
                "category_id": "cat-1",
                "date": "2025-01-15",
            },
        )).content[0].text
    )

    assert result["merchant"]["name"] == name


async def test_create_with_update_balance(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_transaction.return_value = _api_txn()

    await mcp_write_client.call_tool(
        "create_transaction",
        {
            "account_id": "acc-1",
            "amount": -42.50,
            "merchant_name": "Coffee Shop",
            "category_id": "cat-1",
            "date": "2025-01-15",
            "update_balance": True,
        },
    )

    call_kwargs = mock_monarch_client.create_transaction.call_args[1]
    assert call_kwargs["update_balance"] is True


async def test_create_default_update_balance(mcp_write_client, mock_monarch_client):
    mock_monarch_client.create_transaction.return_value = _api_txn()

    await mcp_write_client.call_tool(
        "create_transaction",
        {
            "account_id": "acc-1",
            "amount": -10.0,
            "merchant_name": "Store",
            "category_id": "cat-1",
            "date": "2025-01-15",
        },
    )

    call_kwargs = mock_monarch_client.create_transaction.call_args[1]
    assert call_kwargs["update_balance"] is False


# ===================================================================
# UPDATE (13 tests)
# ===================================================================


async def test_update_notes(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {"id": "txn-1", "notes": "Updated note"}

    result = json.loads(
        (await mcp_write_client.call_tool(
            "update_transaction", {"transaction_id": "txn-1", "notes": "Updated note"}
        )).content[0].text
    )

    assert result["notes"] == "Updated note"
    call_kwargs = mock_monarch_client.update_transaction.call_args[1]
    assert call_kwargs["notes"] == "Updated note"
    assert call_kwargs["transaction_id"] == "txn-1"


async def test_update_noop(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {"id": "txn-1"}

    result = json.loads(
        (await mcp_write_client.call_tool(
            "update_transaction", {"transaction_id": "txn-1"}
        )).content[0].text
    )

    assert result["id"] == "txn-1"
    call_kwargs = mock_monarch_client.update_transaction.call_args[1]
    assert call_kwargs == {"transaction_id": "txn-1"}


async def test_update_amount(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {"id": "txn-1", "amount": -99.99}

    result = json.loads(
        (await mcp_write_client.call_tool(
            "update_transaction", {"transaction_id": "txn-1", "amount": -99.99}
        )).content[0].text
    )

    assert result["amount"] == -99.99


async def test_update_merchant(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {
        "id": "txn-1",
        "merchant": {"name": "New Name"},
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "update_transaction",
            {"transaction_id": "txn-1", "merchant_name": "New Name"},
        )).content[0].text
    )

    assert result["merchant"]["name"] == "New Name"


async def test_update_date(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {"id": "txn-1", "date": "2025-06-15"}

    result = json.loads(
        (await mcp_write_client.call_tool(
            "update_transaction", {"transaction_id": "txn-1", "date": "2025-06-15"}
        )).content[0].text
    )

    assert result["date"] == "2025-06-15"


async def test_update_hide_from_reports(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {
        "id": "txn-1",
        "hideFromReports": True,
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "update_transaction",
            {"transaction_id": "txn-1", "hide_from_reports": True},
        )).content[0].text
    )

    assert result["hideFromReports"] is True
    call_kwargs = mock_monarch_client.update_transaction.call_args[1]
    assert call_kwargs["hide_from_reports"] is True


async def test_update_needs_review(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {
        "id": "txn-1",
        "needsReview": False,
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "update_transaction",
            {"transaction_id": "txn-1", "needs_review": False},
        )).content[0].text
    )

    assert result["needsReview"] is False


async def test_update_multi_field(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {
        "id": "txn-1",
        "amount": -25.0,
        "notes": "multi",
        "date": "2025-02-01",
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "update_transaction",
            {
                "transaction_id": "txn-1",
                "amount": -25.0,
                "notes": "multi",
                "date": "2025-02-01",
            },
        )).content[0].text
    )

    assert result["amount"] == -25.0
    assert result["notes"] == "multi"
    call_kwargs = mock_monarch_client.update_transaction.call_args[1]
    assert call_kwargs["amount"] == -25.0
    assert call_kwargs["notes"] == "multi"
    assert call_kwargs["date"] == "2025-02-01"


async def test_update_category(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {
        "id": "txn-1",
        "category": {"id": "cat-2", "name": "Groceries"},
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "update_transaction",
            {"transaction_id": "txn-1", "category_id": "cat-2"},
        )).content[0].text
    )

    assert result["category"]["name"] == "Groceries"
    call_kwargs = mock_monarch_client.update_transaction.call_args[1]
    assert call_kwargs["category_id"] == "cat-2"


async def test_update_invalid_id(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_transaction.side_effect = Exception(
        "Transaction not found"
    )

    result = (await mcp_write_client.call_tool(
        "update_transaction", {"transaction_id": "bad-id", "notes": "x"}
    )).content[0].text

    assert "Error" in result
    assert "Transaction not found" in result


async def test_update_invalid_date(mcp_write_client, mock_monarch_client):
    mock_monarch_client.update_transaction.side_effect = Exception("Invalid date")

    result = (await mcp_write_client.call_tool(
        "update_transaction", {"transaction_id": "txn-1", "date": "nope"}
    )).content[0].text

    assert "Error" in result


async def test_update_long_notes(mcp_write_client, mock_monarch_client):
    long_note = "N" * 5000
    mock_monarch_client.update_transaction.return_value = {
        "id": "txn-1",
        "notes": long_note,
    }

    result = json.loads(
        (await mcp_write_client.call_tool(
            "update_transaction", {"transaction_id": "txn-1", "notes": long_note}
        )).content[0].text
    )

    assert len(result["notes"]) == 5000


async def test_update_html_xss_merchant(mcp_write_client, mock_monarch_client):
    """WAF blocks HTML-like merchant names with 403 + text/html."""
    cause = Exception("403 Forbidden")
    cause.headers = {"content-type": "text/html"}
    exc = TransportServerError("Forbidden", code=403)
    exc.__cause__ = cause

    mock_monarch_client.update_transaction.side_effect = exc

    result = (await mcp_write_client.call_tool(
        "update_transaction",
        {
            "transaction_id": "txn-1",
            "merchant_name": "<script>alert('xss')</script>",
        },
    )).content[0].text

    # WAF 403 is NOT treated as auth error — just passed through as tool error
    assert "Error" in result


# ===================================================================
# DELETE (3 tests)
# ===================================================================


async def test_delete_happy(mcp_write_client, mock_monarch_client):
    mock_monarch_client.delete_transaction.return_value = None

    result = json.loads(
        (await mcp_write_client.call_tool(
            "delete_transaction", {"transaction_id": "txn-1"}
        )).content[0].text
    )

    assert result["deleted"] is True
    assert result["transaction_id"] == "txn-1"
    mock_monarch_client.delete_transaction.assert_called_once_with("txn-1")


async def test_delete_invalid_id(mcp_write_client, mock_monarch_client):
    mock_monarch_client.delete_transaction.side_effect = Exception(
        "Transaction not found"
    )

    result = (await mcp_write_client.call_tool(
        "delete_transaction", {"transaction_id": "bad-id"}
    )).content[0].text

    assert "Error" in result
    assert "Transaction not found" in result


async def test_delete_already_deleted(mcp_write_client, mock_monarch_client):
    mock_monarch_client.delete_transaction.side_effect = Exception(
        "Transaction does not exist"
    )

    result = (await mcp_write_client.call_tool(
        "delete_transaction", {"transaction_id": "txn-gone"}
    )).content[0].text

    assert "Error" in result
