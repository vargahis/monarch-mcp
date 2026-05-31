"""Live e2e tests for recurring-merchant tools — read-tool edges + live error paths.

``find_merchant_id_by_name`` is a read tool, so its distinct-merchant / limit /
empty-result behaviour is exercised directly against the live API. The write tool
``update_recurring_merchant`` is exercised on its **invalid-id error path** and on a
**self-restoring partial-edit round-trip** (mark recurring → switch off → re-price →
clear). The round-trip only ever touches a merchant that is *not already recurring*
and restores it to non-recurring in a ``finally`` block, so a real bill is never left
mutated — this is the regression guard for the bug where a partial edit that omitted
``is_recurring`` was rejected by Monarch with an opaque error.
"""
# pylint: disable=missing-function-docstring,redefined-outer-name

import pytest

pytestmark = pytest.mark.integration

# Wide window so an existing recurrence (even off-cycle) is detected before we pick a
# merchant to mutate — get_recurring_transactions is date-bound, so a narrow range
# could miss a real bill and risk clobbering it.
_RECURRING_SCAN_START = "2025-01-01"
_RECURRING_SCAN_END = "2026-12-31"


@pytest.fixture
async def a_merchant_name(live_mcp_client, call_json):
    """A merchant name pulled from recent transactions (skip if the account has none)."""
    txns = await call_json(live_mcp_client, "get_transactions", {"limit": 50})
    for txn in txns:
        name = txn.get("merchant")
        if name:
            return name
    pytest.skip("live account has no transactions with a merchant to search for")


@pytest.fixture
async def non_recurring_merchant(live_write_client, call_json):
    """A real merchant that is NOT currently recurring, as ``(id, name)``.

    Mutating an already-recurring merchant would risk the user's real bill, so we
    pick one absent from the (wide-window) recurring list and the test restores it to
    non-recurring afterwards. Skips if the account has no safe candidate.
    """
    recurring = await call_json(
        live_write_client,
        "get_recurring_transactions",
        {"start_date": _RECURRING_SCAN_START, "end_date": _RECURRING_SCAN_END},
    )
    items = recurring.get("recurringTransactionItems", []) if isinstance(recurring, dict) else []
    recurring_ids = {
        ((item.get("stream") or {}).get("merchant") or {}).get("id") for item in items
    }

    txns = await call_json(live_write_client, "get_transactions", {"limit": 50})
    seen_names = []
    for txn in txns:
        name = txn.get("merchant")
        if name and name not in seen_names:
            seen_names.append(name)

    for name in seen_names:
        merchants = await call_json(
            live_write_client, "find_merchant_id_by_name", {"name": name, "limit": 5}
        )
        for merchant in merchants:
            mid = merchant.get("merchant_id")
            if mid and mid not in recurring_ids:
                return mid, merchant.get("merchant_name") or name
    pytest.skip("live account has no non-recurring merchant to safely mutate")


async def test_find_merchant_id_by_name_distinct(live_mcp_client, call_json, a_merchant_name):
    merchants = await call_json(
        live_mcp_client, "find_merchant_id_by_name", {"name": a_merchant_name}
    )
    assert isinstance(merchants, list)
    assert merchants, f"no merchants found for a name taken from a real txn: {a_merchant_name!r}"
    ids = [m["merchant_id"] for m in merchants]
    assert all(ids), merchants               # every entry carries a non-empty merchant_id
    assert len(ids) == len(set(ids)), ids    # ids are distinct (deduped by the tool)


async def test_find_merchant_id_by_name_respects_limit(
    live_mcp_client, call_json, a_merchant_name
):
    merchants = await call_json(
        live_mcp_client, "find_merchant_id_by_name", {"name": a_merchant_name, "limit": 1}
    )
    assert isinstance(merchants, list)
    assert len(merchants) <= 1


async def test_find_merchant_id_by_name_empty_for_nonsense(live_mcp_client, call_json):
    merchants = await call_json(
        live_mcp_client,
        "find_merchant_id_by_name",
        {"name": "zzzz-no-such-merchant-zzzz-MCP-Test"},
    )
    assert merchants == []


async def test_update_recurring_merchant_invalid_id_is_graceful(
    live_write_client, call_text, maybe_json
):
    text = await call_text(
        live_write_client,
        "update_recurring_merchant",
        {
            "merchant_id": "000000000000000000",
            "name": "MCP-Test-NoSuchMerchant",
            "is_recurring": False,
        },
    )
    # Robustness contract: a bogus merchant id must not leak a raw traceback. The tool
    # returns either a decorator "Error ..." string or a parseable JSON payload (a
    # rejection dict, or a benign object if Monarch no-ops the unknown id).
    assert "Traceback" not in text, text[:300]
    data = maybe_json(text)
    assert text.startswith("Error ") or isinstance(data, (dict, list)), text[:300]


async def test_update_recurring_merchant_partial_edits_round_trip(
    live_write_client, call_json, non_recurring_merchant
):
    """Mark recurring → switch off → re-price → clear, restoring the merchant.

    The switch-off and re-price steps are partial edits: they pass only the field
    being changed plus the now-mandatory ``is_recurring=True``. Before the fix these
    omitted ``is_recurring`` and Monarch rejected them with an opaque error.
    """
    merchant_id, merchant_name = non_recurring_merchant
    base = {"merchant_id": merchant_id, "name": merchant_name}

    try:
        full = await call_json(
            live_write_client,
            "update_recurring_merchant",
            {**base, "is_recurring": True, "frequency": "monthly",
             "base_date": "2025-01-15", "amount": -9.99, "is_active": True},
        )
        stream = full["updateMerchant"]["merchant"]["recurringTransactionStream"]
        assert stream is not None, full
        assert stream["isActive"] is True
        assert stream["amount"] == pytest.approx(-9.99)

        # Partial edit #1 — switch the bill off; Monarch keeps the schedule.
        off = await call_json(
            live_write_client,
            "update_recurring_merchant",
            {**base, "is_recurring": True, "is_active": False},
        )
        assert off["updateMerchant"]["errors"] is None, off
        assert off["updateMerchant"]["merchant"]["recurringTransactionStream"]["isActive"] is False

        # Partial edit #2 — change just the amount (and switch back on).
        repriced = await call_json(
            live_write_client,
            "update_recurring_merchant",
            {**base, "is_recurring": True, "is_active": True, "amount": -12.49},
        )
        stream = repriced["updateMerchant"]["merchant"]["recurringTransactionStream"]
        assert stream["amount"] == pytest.approx(-12.49)
        assert stream["isActive"] is True
    finally:
        # Restore: clear the recurring flag so the merchant is non-recurring again.
        cleared = await call_json(
            live_write_client,
            "update_recurring_merchant",
            {**base, "is_recurring": False},
        )
        assert cleared["updateMerchant"]["merchant"]["recurringTransactionStream"] is None
