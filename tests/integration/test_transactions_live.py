"""Live e2e tests for transaction tools — robustness + live error paths.

Update/stress cases operate on a throwaway ``MCP-Test-`` transaction (created,
mutated, deleted) — never on the user's real transactions, so there is nothing
to revert.
"""
# pylint: disable=missing-function-docstring,redefined-outer-name

import json

import pytest

pytestmark = pytest.mark.integration


async def _create_txn(client, call_json, extract_id, account_id, category_id, **overrides):
    """Create a throwaway MCP-Test- transaction; return (id, raw_result)."""
    args = {
        "account_id": account_id,
        "amount": -12.34,
        "merchant_name": "MCP-Test-Txn",
        "category_id": category_id,
        "date": "2026-01-15",
    }
    args.update(overrides)
    result = await call_json(client, "create_transaction", args)
    return extract_id(result), result


# ── happy path ─────────────────────────────────────────────────────────

async def test_create_transaction_happy_path_and_cleanup(
    live_write_client, call_json, extract_id, checking_account_id, category_id
):
    txn_id, result = await _create_txn(
        live_write_client, call_json, extract_id,
        checking_account_id, category_id,
        amount=-15.50, merchant_name="MCP-Test-Coffee-Shop",
        notes="MCP-Test e2e happy path",
    )
    assert txn_id, f"expected a created transaction id, got: {result}"
    try:
        details = await call_json(
            live_write_client, "get_transaction_details", {"transaction_id": txn_id}
        )
        assert "MCP-Test-Coffee-Shop" in json.dumps(details)
    finally:
        deleted = await call_json(
            live_write_client, "delete_transaction", {"transaction_id": txn_id}
        )
        assert deleted == {"deleted": True, "transaction_id": txn_id}


# ── robustness: adversarial create inputs ──────────────────────────────

@pytest.mark.parametrize(
    "label,overrides",
    [
        ("large_amount", {"amount": -999999999.99, "merchant_name": "MCP-Test-Large-Amount"}),
        ("unicode_merchant", {"amount": -8.00, "merchant_name": "MCP-Test-カフェ-☕"}),
    ],
)
async def test_create_transaction_adversarial_input_is_graceful(
    live_write_client, call_text, extract_id, maybe_json,
    checking_account_id, category_id, label, overrides,
):
    args = {
        "account_id": checking_account_id,
        "category_id": category_id,
        "date": "2026-01-15",
        "amount": -1.00,
        "merchant_name": f"MCP-Test-{label}",
    }
    args.update(overrides)
    text = await call_text(live_write_client, "create_transaction", args)

    # The MCP layer must never crash — either a created object or a clean error.
    assert "Traceback" not in text, text[:300]
    data = maybe_json(text)
    created_id = extract_id(data) if data is not None else None
    if created_id:
        await live_write_client.call_tool(
            "delete_transaction", {"transaction_id": created_id}
        )
    else:
        assert (isinstance(data, dict) and "error" in data) or text.startswith("Error "), \
            f"expected created object or graceful error, got: {text[:300]}"


# ── robustness: update with adversarial inputs (throwaway txn) ──────────

@pytest.mark.parametrize(
    "label,update_args_fn",
    [
        ("long_notes", lambda: {"notes": "MCP-Test-" + "X" * 1000}),
        ("html_merchant", lambda: {"merchant_name": "MCP-Test-<script>alert('xss')</script>"}),
    ],
)
async def test_update_transaction_adversarial_input_is_graceful(
    live_write_client, call_json, call_text, extract_id, maybe_json,
    checking_account_id, category_id, label, update_args_fn,
):
    txn_id, result = await _create_txn(
        live_write_client, call_json, extract_id, checking_account_id, category_id
    )
    assert txn_id, f"setup failed to create throwaway txn: {result}"
    try:
        args = {"transaction_id": txn_id, **update_args_fn()}
        text = await call_text(live_write_client, "update_transaction", args)
        # Monarch's WAF may 403 on <script>; both success and a clean error are OK.
        assert "Traceback" not in text, text[:300]
        data = maybe_json(text)
        assert data is not None or text.startswith("Error "), \
            f"expected JSON or graceful error, got: {text[:300]}"
    finally:
        await live_write_client.call_tool(
            "delete_transaction", {"transaction_id": txn_id}
        )


# ── live error path: server-side invalid date on create ────────────────

async def test_create_transaction_invalid_date_is_graceful(
    live_write_client, call_text, maybe_json, extract_id, checking_account_id, category_id
):
    text = await call_text(
        live_write_client, "create_transaction",
        {
            "account_id": checking_account_id,
            "amount": -10.00,
            "merchant_name": "MCP-Test-Bad-Date",
            "category_id": category_id,
            "date": "not-a-date",
        },
    )
    assert "Traceback" not in text, text[:300]
    data = maybe_json(text)
    created_id = extract_id(data) if data is not None else None
    if created_id:
        # If the API unexpectedly accepted it, don't leave residue.
        await live_write_client.call_tool(
            "delete_transaction", {"transaction_id": created_id}
        )
        pytest.fail("expected invalid date to be rejected, but a transaction was created")
    assert (isinstance(data, dict) and "error" in data) or text.startswith("Error "), text[:300]


# ── robustness: pagination edge cases (read-only) ──────────────────────

@pytest.mark.parametrize(
    "args",
    [
        {"limit": 10, "offset": 999999},
        {"limit": 0},
        {"limit": -1},
        {"limit": 10, "offset": -1},
        {"limit": 10000},
    ],
)
async def test_get_transactions_pagination_edges_are_graceful(
    live_mcp_client, call_text, maybe_json, args
):
    text = await call_text(live_mcp_client, "get_transactions", args)
    assert "Traceback" not in text, text[:300]
    data = maybe_json(text)
    # Either a list of results, an {"error": ...} object, or a clean error string.
    assert isinstance(data, list) or (isinstance(data, dict) and "error" in data) \
        or text.startswith("Error "), f"unexpected response: {text[:300]}"
