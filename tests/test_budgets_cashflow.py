"""Phase 4: Budget and cashflow tool tests (12 tests)."""
# pylint: disable=missing-function-docstring

import json


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


async def test_budgets_both_dates(mcp_client, mock_monarch_client):
    mock_monarch_client.get_budgets.return_value = SAMPLE_BUDGET

    result = json.loads(
        (await mcp_client.call_tool(
            "get_budgets", {"start_date": "2025-01-01", "end_date": "2025-01-31"}
        )).content[0].text
    )

    assert "budgetData" in result
    mock_monarch_client.get_budgets.assert_called_once_with(
        use_v2_goals=True, start_date="2025-01-01", end_date="2025-01-31"
    )


async def test_budgets_no_dates(mcp_client, mock_monarch_client):
    mock_monarch_client.get_budgets.return_value = SAMPLE_BUDGET

    result = json.loads((await mcp_client.call_tool("get_budgets")).content[0].text)

    assert "budgetData" in result
    mock_monarch_client.get_budgets.assert_called_once_with(use_v2_goals=True)


async def test_budgets_only_start(mcp_client):
    result = json.loads(
        (await mcp_client.call_tool("get_budgets", {"start_date": "2025-01-01"})).content[0].text
    )
    assert "error" in result


async def test_budgets_only_end(mcp_client):
    result = json.loads(
        (await mcp_client.call_tool("get_budgets", {"end_date": "2025-01-31"})).content[0].text
    )
    assert "error" in result


async def test_budgets_invalid_format(mcp_client, mock_monarch_client):
    mock_monarch_client.get_budgets.side_effect = Exception("Invalid date")

    result = (await mcp_client.call_tool(
        "get_budgets", {"start_date": "bad", "end_date": "bad"}
    )).content[0].text

    assert "Error" in result
    assert "Invalid date" in result


async def test_budgets_future_dates(mcp_client, mock_monarch_client):
    mock_monarch_client.get_budgets.return_value = {"budgetData": None}

    result = json.loads(
        (await mcp_client.call_tool(
            "get_budgets", {"start_date": "2099-01-01", "end_date": "2099-12-31"}
        )).content[0].text
    )

    assert result["budgetData"] is None


async def test_budgets_v2_goals_default(mcp_client, mock_monarch_client):
    mock_monarch_client.get_budgets.return_value = SAMPLE_BUDGET

    await mcp_client.call_tool("get_budgets")

    mock_monarch_client.get_budgets.assert_called_once_with(use_v2_goals=True)


async def test_budgets_v2_goals_disabled(mcp_client, mock_monarch_client):
    mock_monarch_client.get_budgets.return_value = SAMPLE_BUDGET

    await mcp_client.call_tool("get_budgets", {"use_v2_goals": False})

    mock_monarch_client.get_budgets.assert_called_once_with(use_v2_goals=False)


# ===================================================================
# get_cashflow (6 tests)
# ===================================================================


async def test_cashflow_both_dates(mcp_client, mock_monarch_client):
    mock_monarch_client.get_cashflow.return_value = SAMPLE_CASHFLOW

    result = json.loads(
        (await mcp_client.call_tool(
            "get_cashflow", {"start_date": "2025-01-01", "end_date": "2025-01-31"}
        )).content[0].text
    )

    assert "summary" in result
    mock_monarch_client.get_cashflow.assert_called_once_with(
        start_date="2025-01-01", end_date="2025-01-31"
    )


async def test_cashflow_no_dates(mcp_client, mock_monarch_client):
    mock_monarch_client.get_cashflow.return_value = SAMPLE_CASHFLOW

    result = json.loads((await mcp_client.call_tool("get_cashflow")).content[0].text)

    assert "summary" in result
    mock_monarch_client.get_cashflow.assert_called_once_with()


async def test_cashflow_only_start(mcp_client):
    result = json.loads(
        (await mcp_client.call_tool("get_cashflow", {"start_date": "2025-01-01"})).content[0].text
    )
    assert "error" in result


async def test_cashflow_only_end(mcp_client):
    result = json.loads(
        (await mcp_client.call_tool("get_cashflow", {"end_date": "2025-01-31"})).content[0].text
    )
    assert "error" in result


async def test_cashflow_invalid_format(mcp_client, mock_monarch_client):
    mock_monarch_client.get_cashflow.side_effect = Exception("Invalid date")

    result = (await mcp_client.call_tool(
        "get_cashflow", {"start_date": "bad", "end_date": "bad"}
    )).content[0].text

    assert "Error" in result
    assert "Invalid date" in result


async def test_cashflow_future_dates(mcp_client, mock_monarch_client):
    mock_monarch_client.get_cashflow.return_value = {"summary": []}

    result = json.loads(
        (await mcp_client.call_tool(
            "get_cashflow", {"start_date": "2099-01-01", "end_date": "2099-12-31"}
        )).content[0].text
    )

    assert result["summary"] == []
