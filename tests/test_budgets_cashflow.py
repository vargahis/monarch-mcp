"""Phase 4: Budget and cashflow tool tests (12 tests)."""
# pylint: disable=missing-function-docstring

import json

from monarch_mcp_server.server import get_budgets, get_cashflow

SAMPLE_BUDGET = {
    "budgetData": {
        "totalBudgetAmount": {"amount": 5000},
        "totalActualAmount": {"amount": 3200},
    }
}

SAMPLE_CASHFLOW = {
    "summary": [{"summary": {"sumIncome": 6000, "sumExpense": -4000, "savings": 2000}}]
}


# ===================================================================
# get_budgets (6 tests)
# ===================================================================


def test_budgets_both_dates(mock_monarch_client):
    mock_monarch_client.get_budgets.return_value = SAMPLE_BUDGET

    result = json.loads(get_budgets(start_date="2025-01-01", end_date="2025-01-31"))

    assert "budgetData" in result
    mock_monarch_client.get_budgets.assert_called_once_with(
        start_date="2025-01-01", end_date="2025-01-31"
    )


def test_budgets_no_dates(mock_monarch_client):
    mock_monarch_client.get_budgets.return_value = SAMPLE_BUDGET

    result = json.loads(get_budgets())

    assert "budgetData" in result
    mock_monarch_client.get_budgets.assert_called_once_with()


def test_budgets_only_start():
    result = json.loads(get_budgets(start_date="2025-01-01"))
    assert "error" in result


def test_budgets_only_end():
    result = json.loads(get_budgets(end_date="2025-01-31"))
    assert "error" in result


def test_budgets_invalid_format(mock_monarch_client):
    mock_monarch_client.get_budgets.side_effect = Exception("Invalid date")

    result = get_budgets(start_date="bad", end_date="bad")

    assert "Error" in result
    assert "Invalid date" in result


def test_budgets_future_dates(mock_monarch_client):
    mock_monarch_client.get_budgets.return_value = {"budgetData": None}

    result = json.loads(
        get_budgets(start_date="2099-01-01", end_date="2099-12-31")
    )

    assert result["budgetData"] is None


# ===================================================================
# get_cashflow (6 tests)
# ===================================================================


def test_cashflow_both_dates(mock_monarch_client):
    mock_monarch_client.get_cashflow.return_value = SAMPLE_CASHFLOW

    result = json.loads(
        get_cashflow(start_date="2025-01-01", end_date="2025-01-31")
    )

    assert "summary" in result
    mock_monarch_client.get_cashflow.assert_called_once_with(
        start_date="2025-01-01", end_date="2025-01-31"
    )


def test_cashflow_no_dates(mock_monarch_client):
    mock_monarch_client.get_cashflow.return_value = SAMPLE_CASHFLOW

    result = json.loads(get_cashflow())

    assert "summary" in result
    mock_monarch_client.get_cashflow.assert_called_once_with()


def test_cashflow_only_start():
    result = json.loads(get_cashflow(start_date="2025-01-01"))
    assert "error" in result


def test_cashflow_only_end():
    result = json.loads(get_cashflow(end_date="2025-01-31"))
    assert "error" in result


def test_cashflow_invalid_format(mock_monarch_client):
    mock_monarch_client.get_cashflow.side_effect = Exception("Invalid date")

    result = get_cashflow(start_date="bad", end_date="bad")

    assert "Error" in result
    assert "Invalid date" in result


def test_cashflow_future_dates(mock_monarch_client):
    mock_monarch_client.get_cashflow.return_value = {"summary": []}

    result = json.loads(
        get_cashflow(start_date="2099-01-01", end_date="2099-12-31")
    )

    assert result["summary"] == []
