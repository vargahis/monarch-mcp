"""Phase 6: Transaction CRUD tests (25 tests)."""

import json

from gql.transport.exceptions import TransportServerError

from monarch_mcp_server.server import (
    create_transaction,
    update_transaction,
    delete_transaction,
)


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


def test_create_happy(mock_monarch_client):
    mock_monarch_client.create_transaction.return_value = _api_txn()

    result = json.loads(
        create_transaction(
            account_id="acc-1",
            amount=-42.50,
            merchant_name="Coffee Shop",
            category_id="cat-1",
            date="2025-01-15",
            notes="Morning coffee",
        )
    )

    assert result["id"] == "txn-new"
    mock_monarch_client.create_transaction.assert_called_once_with(
        date="2025-01-15",
        account_id="acc-1",
        amount=-42.50,
        merchant_name="Coffee Shop",
        category_id="cat-1",
        notes="Morning coffee",
    )


def test_create_positive_amount(mock_monarch_client):
    mock_monarch_client.create_transaction.return_value = _api_txn(amount=500.00)

    result = json.loads(
        create_transaction(
            account_id="acc-1",
            amount=500.00,
            merchant_name="Employer",
            category_id="cat-income",
            date="2025-01-15",
        )
    )

    assert result["amount"] == 500.00


def test_create_no_notes(mock_monarch_client):
    mock_monarch_client.create_transaction.return_value = _api_txn()

    create_transaction(
        account_id="acc-1",
        amount=-10.0,
        merchant_name="Store",
        category_id="cat-1",
        date="2025-01-15",
    )

    # notes defaults to "" when not provided
    call_kwargs = mock_monarch_client.create_transaction.call_args[1]
    assert call_kwargs["notes"] == ""


def test_create_invalid_account(mock_monarch_client):
    mock_monarch_client.create_transaction.side_effect = Exception(
        "Account not found"
    )

    result = create_transaction(
        account_id="bad-acc",
        amount=-10.0,
        merchant_name="Store",
        category_id="cat-1",
        date="2025-01-15",
    )

    assert "Error" in result
    assert "Account not found" in result


def test_create_invalid_category(mock_monarch_client):
    mock_monarch_client.create_transaction.side_effect = Exception(
        "Category not found"
    )

    result = create_transaction(
        account_id="acc-1",
        amount=-10.0,
        merchant_name="Store",
        category_id="bad-cat",
        date="2025-01-15",
    )

    assert "Error" in result
    assert "Category not found" in result


def test_create_invalid_date(mock_monarch_client):
    mock_monarch_client.create_transaction.side_effect = Exception("Invalid date")

    result = create_transaction(
        account_id="acc-1",
        amount=-10.0,
        merchant_name="Store",
        category_id="cat-1",
        date="not-a-date",
    )

    assert "Error" in result


def test_create_zero_amount(mock_monarch_client):
    mock_monarch_client.create_transaction.return_value = _api_txn(amount=0.0)

    result = json.loads(
        create_transaction(
            account_id="acc-1",
            amount=0.0,
            merchant_name="Adjustment",
            category_id="cat-1",
            date="2025-01-15",
        )
    )

    assert result["amount"] == 0.0


def test_create_large_amount(mock_monarch_client):
    big = 9999999.99
    mock_monarch_client.create_transaction.return_value = _api_txn(amount=big)

    result = json.loads(
        create_transaction(
            account_id="acc-1",
            amount=big,
            merchant_name="Mega Corp",
            category_id="cat-1",
            date="2025-01-15",
        )
    )

    assert result["amount"] == big


def test_create_unicode_merchant(mock_monarch_client):
    name = "\u5496\u5561\u5e97 \u2615"
    mock_monarch_client.create_transaction.return_value = _api_txn(
        merchant={"name": name}
    )

    result = json.loads(
        create_transaction(
            account_id="acc-1",
            amount=-5.0,
            merchant_name=name,
            category_id="cat-1",
            date="2025-01-15",
        )
    )

    assert result["merchant"]["name"] == name


# ===================================================================
# UPDATE (13 tests)
# ===================================================================


def test_update_notes(mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {"id": "txn-1", "notes": "Updated note"}

    result = json.loads(
        update_transaction(transaction_id="txn-1", notes="Updated note")
    )

    assert result["notes"] == "Updated note"
    call_kwargs = mock_monarch_client.update_transaction.call_args[1]
    assert call_kwargs["notes"] == "Updated note"
    assert call_kwargs["transaction_id"] == "txn-1"


def test_update_noop(mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {"id": "txn-1"}

    result = json.loads(update_transaction(transaction_id="txn-1"))

    assert result["id"] == "txn-1"
    call_kwargs = mock_monarch_client.update_transaction.call_args[1]
    assert call_kwargs == {"transaction_id": "txn-1"}


def test_update_amount(mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {"id": "txn-1", "amount": -99.99}

    result = json.loads(
        update_transaction(transaction_id="txn-1", amount=-99.99)
    )

    assert result["amount"] == -99.99


def test_update_merchant(mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {
        "id": "txn-1",
        "merchant": {"name": "New Name"},
    }

    result = json.loads(
        update_transaction(transaction_id="txn-1", merchant_name="New Name")
    )

    assert result["merchant"]["name"] == "New Name"


def test_update_date(mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {"id": "txn-1", "date": "2025-06-15"}

    result = json.loads(
        update_transaction(transaction_id="txn-1", date="2025-06-15")
    )

    assert result["date"] == "2025-06-15"


def test_update_hide_from_reports(mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {
        "id": "txn-1",
        "hideFromReports": True,
    }

    result = json.loads(
        update_transaction(transaction_id="txn-1", hide_from_reports=True)
    )

    assert result["hideFromReports"] is True
    call_kwargs = mock_monarch_client.update_transaction.call_args[1]
    assert call_kwargs["hide_from_reports"] is True


def test_update_needs_review(mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {
        "id": "txn-1",
        "needsReview": False,
    }

    result = json.loads(
        update_transaction(transaction_id="txn-1", needs_review=False)
    )

    assert result["needsReview"] is False


def test_update_multi_field(mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {
        "id": "txn-1",
        "amount": -25.0,
        "notes": "multi",
        "date": "2025-02-01",
    }

    result = json.loads(
        update_transaction(
            transaction_id="txn-1", amount=-25.0, notes="multi", date="2025-02-01"
        )
    )

    assert result["amount"] == -25.0
    assert result["notes"] == "multi"
    call_kwargs = mock_monarch_client.update_transaction.call_args[1]
    assert call_kwargs["amount"] == -25.0
    assert call_kwargs["notes"] == "multi"
    assert call_kwargs["date"] == "2025-02-01"


def test_update_category(mock_monarch_client):
    mock_monarch_client.update_transaction.return_value = {
        "id": "txn-1",
        "category": {"id": "cat-2", "name": "Groceries"},
    }

    result = json.loads(
        update_transaction(transaction_id="txn-1", category_id="cat-2")
    )

    assert result["category"]["name"] == "Groceries"
    call_kwargs = mock_monarch_client.update_transaction.call_args[1]
    assert call_kwargs["category_id"] == "cat-2"


def test_update_invalid_id(mock_monarch_client):
    mock_monarch_client.update_transaction.side_effect = Exception(
        "Transaction not found"
    )

    result = update_transaction(transaction_id="bad-id", notes="x")

    assert "Error" in result
    assert "Transaction not found" in result


def test_update_invalid_date(mock_monarch_client):
    mock_monarch_client.update_transaction.side_effect = Exception("Invalid date")

    result = update_transaction(transaction_id="txn-1", date="nope")

    assert "Error" in result


def test_update_long_notes(mock_monarch_client):
    long_note = "N" * 5000
    mock_monarch_client.update_transaction.return_value = {
        "id": "txn-1",
        "notes": long_note,
    }

    result = json.loads(
        update_transaction(transaction_id="txn-1", notes=long_note)
    )

    assert len(result["notes"]) == 5000


def test_update_html_xss_merchant(mock_monarch_client):
    """WAF blocks HTML-like merchant names with 403 + text/html."""
    cause = Exception("403 Forbidden")
    cause.headers = {"content-type": "text/html"}
    exc = TransportServerError("Forbidden", code=403)
    exc.__cause__ = cause

    mock_monarch_client.update_transaction.side_effect = exc

    result = update_transaction(
        transaction_id="txn-1",
        merchant_name="<script>alert('xss')</script>",
    )

    # WAF 403 is NOT treated as auth error — just passed through as tool error
    assert "Error" in result


# ===================================================================
# DELETE (3 tests)
# ===================================================================


def test_delete_happy(mock_monarch_client):
    mock_monarch_client.delete_transaction.return_value = None

    result = json.loads(delete_transaction(transaction_id="txn-1"))

    assert result["deleted"] is True
    assert result["transaction_id"] == "txn-1"
    mock_monarch_client.delete_transaction.assert_called_once_with("txn-1")


def test_delete_invalid_id(mock_monarch_client):
    mock_monarch_client.delete_transaction.side_effect = Exception(
        "Transaction not found"
    )

    result = delete_transaction(transaction_id="bad-id")

    assert "Error" in result
    assert "Transaction not found" in result


def test_delete_already_deleted(mock_monarch_client):
    mock_monarch_client.delete_transaction.side_effect = Exception(
        "Transaction does not exist"
    )

    result = delete_transaction(transaction_id="txn-gone")

    assert "Error" in result
