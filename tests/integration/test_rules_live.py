"""Live e2e tests for transaction-rule tools — lifecycle + REPLACE semantics + errors.

Covers the full rule surface (category, tag, merchant-rename, amount, split) as
full create -> read-back -> delete lifecycles, and verifies Monarch's
REPLACE-semantics update by checking that updating one field preserves the rest.
The amount/split payloads use Monarch's real enums (``amountCriteria.operator``
is gt/lt/eq; ``SplitAmountType`` is ABSOLUTE/PERCENTAGE).

Every test rule carries an ``MCP-Test-`` merchant criterion so the conftest
name-prefix sweep can reclaim it even if a test crashes. Monarch lowercases rule
criteria values, so a rule created with "MCP-Test-..." reads back as "mcp-test-...".
"""
# pylint: disable=missing-function-docstring,redefined-outer-name

import pytest

pytestmark = pytest.mark.integration


def _find_rule_id(rules, needle):
    needle = needle.lower()
    for rule in rules:
        values = [c.get("value", "") for c in (rule.get("merchant_name_criteria") or [])]
        values += [c.get("value", "") for c in (rule.get("original_statement_criteria") or [])]
        if any(needle in (v or "").lower() for v in values):
            return rule.get("id")
    return None


def _rule_by_id(rules, rule_id):
    return next((r for r in rules if r.get("id") == rule_id), None)


async def _create(client, call_text, maybe_json, rule):
    """Create a rule via the typed schema; return the parsed response."""
    return maybe_json(
        await call_text(client, "create_transaction_rule", {"rule": rule})
    )


async def _delete(client, call_text, maybe_json, rule_id):
    deleted = maybe_json(
        await call_text(client, "delete_transaction_rule", {"rule_id": rule_id})
    )
    assert deleted == {"deleted": True, "rule_id": rule_id}, deleted


# ── full-success lifecycles (confident payload shapes) ─────────────────


async def test_category_rule_lifecycle(
    live_write_client, call_json, call_text, maybe_json, category_id
):
    merchant = "MCP-Test-Rule-Category"
    created = await _create(live_write_client, call_text, maybe_json, {
        "merchantNameCriteria": [{"operator": "contains", "value": merchant}],
        "setCategoryAction": category_id,
    })
    assert isinstance(created, dict) and created.get("created") is True, created

    rule_id = None
    try:
        rules = await call_json(live_write_client, "get_transaction_rules")
        rule_id = _find_rule_id(rules, merchant)
        assert rule_id, f"created rule not found: {rules}"
        assert _rule_by_id(rules, rule_id)["set_category_id"] == category_id
    finally:
        if rule_id:
            await _delete(live_write_client, call_text, maybe_json, rule_id)

    rules_after = await call_json(live_write_client, "get_transaction_rules")
    assert _find_rule_id(rules_after, merchant) is None


async def test_tag_rule_lifecycle(
    live_write_client, call_json, call_text, maybe_json, category_id, tag_id
):
    merchant = "MCP-Test-Rule-Tag-Match"
    created = await _create(live_write_client, call_text, maybe_json, {
        "merchantNameCriteria": [{"operator": "contains", "value": merchant}],
        "setCategoryAction": category_id,
        "addTagsAction": [tag_id],
    })
    assert isinstance(created, dict) and created.get("created") is True, created

    rule_id = None
    try:
        rules = await call_json(live_write_client, "get_transaction_rules")
        rule_id = _find_rule_id(rules, merchant)
        assert rule_id, f"created rule not found: {rules}"
        assert tag_id in (_rule_by_id(rules, rule_id)["add_tag_ids"] or [])
    finally:
        if rule_id:
            await _delete(live_write_client, call_text, maybe_json, rule_id)


async def test_merchant_rename_rule_lifecycle(
    live_write_client, call_json, call_text, maybe_json
):
    merchant = "MCP-Test-Rule-Rename"
    created = await _create(live_write_client, call_text, maybe_json, {
        "merchantNameCriteria": [{"operator": "contains", "value": merchant}],
        "setMerchantAction": "MCP-Test-Renamed-Merchant",
    })
    assert isinstance(created, dict) and created.get("created") is True, created

    rule_id = None
    try:
        rules = await call_json(live_write_client, "get_transaction_rules")
        rule_id = _find_rule_id(rules, merchant)
        assert rule_id, f"created rule not found: {rules}"
        assert _rule_by_id(rules, rule_id)["set_merchant_name"] == "MCP-Test-Renamed-Merchant"
    finally:
        if rule_id:
            await _delete(live_write_client, call_text, maybe_json, rule_id)


# ── REPLACE semantics: update one field, the rest survives ─────────────


async def test_update_preserves_untouched_fields(
    live_write_client, call_json, call_text, maybe_json,
    category_id, second_category_id, tag_id,
):
    merchant = "MCP-Test-Rule-Update"
    created = await _create(live_write_client, call_text, maybe_json, {
        "merchantNameCriteria": [{"operator": "contains", "value": merchant}],
        "setCategoryAction": category_id,
        "addTagsAction": [tag_id],
    })
    assert isinstance(created, dict) and created.get("created") is True, created

    rule_id = None
    try:
        rules = await call_json(live_write_client, "get_transaction_rules")
        rule_id = _find_rule_id(rules, merchant)
        assert rule_id, f"created rule not found: {rules}"

        # Update ONLY the category.
        updated = maybe_json(await call_text(
            live_write_client, "update_transaction_rule",
            {"rule_id": rule_id, "overrides": {"setCategoryAction": second_category_id}},
        ))
        assert isinstance(updated, dict) and updated.get("updated") is True, updated

        after = _rule_by_id(
            await call_json(live_write_client, "get_transaction_rules"), rule_id,
        )
        # Category changed...
        assert after["set_category_id"] == second_category_id
        # ...but the tag and merchant criterion were preserved (REPLACE-safe).
        assert tag_id in (after["add_tag_ids"] or [])
        assert _find_rule_id([after], merchant) == rule_id
    finally:
        if rule_id:
            await _delete(live_write_client, call_text, maybe_json, rule_id)


# ── deeper nested shapes (verified valid against the live SplitAmountType) ──


async def test_amount_rule_lifecycle(
    live_write_client, call_json, call_text, maybe_json, category_id
):
    merchant = "MCP-Test-Rule-Amount"
    created = await _create(live_write_client, call_text, maybe_json, {
        "merchantNameCriteria": [{"operator": "contains", "value": merchant}],
        "setCategoryAction": category_id,
        # amountCriteria.operator is gt / lt / eq (Monarch rejects other forms).
        "amountCriteria": {"operator": "gt", "isExpense": True, "value": 100},
    })
    assert isinstance(created, dict) and created.get("created") is True, created

    rule_id = None
    try:
        rules = await call_json(live_write_client, "get_transaction_rules")
        rule_id = _find_rule_id(rules, merchant)
        assert rule_id, f"created rule not found: {rules}"
        amount = _rule_by_id(rules, rule_id)["amount_criteria"]
        assert amount and amount.get("operator") == "gt"
    finally:
        if rule_id:
            await _delete(live_write_client, call_text, maybe_json, rule_id)


async def test_split_rule_lifecycle(
    live_write_client, call_json, call_text, maybe_json, category_id, second_category_id
):
    merchant = "MCP-Test-Rule-Split"
    created = await _create(live_write_client, call_text, maybe_json, {
        "merchantNameCriteria": [{"operator": "contains", "value": merchant}],
        # SplitAmountType is ABSOLUTE | PERCENTAGE; PERCENTAGE amounts are
        # fractions that must sum to 1, and at least two splits are required.
        "splitTransactionsAction": {
            "amountType": "PERCENTAGE",
            "splitsInfo": [
                {"categoryId": category_id, "amount": 0.6},
                {"categoryId": second_category_id, "amount": 0.4},
            ],
        },
    })
    assert isinstance(created, dict) and created.get("created") is True, created

    rule_id = None
    try:
        rules = await call_json(live_write_client, "get_transaction_rules")
        rule_id = _find_rule_id(rules, merchant)
        assert rule_id, f"created rule not found: {rules}"
        split = _rule_by_id(rules, rule_id)["split_transactions_action"]
        assert split and split.get("amountType") == "PERCENTAGE"
    finally:
        if rule_id:
            await _delete(live_write_client, call_text, maybe_json, rule_id)


# ── live error paths ───────────────────────────────────────────────────


async def test_update_invalid_id_is_graceful(live_write_client, call_text, maybe_json):
    text = await call_text(
        live_write_client, "update_transaction_rule",
        {"rule_id": "000000000000000000", "overrides": {"setCategoryAction": "1"}},
    )
    assert "Traceback" not in text, text[:300]
    data = maybe_json(text)
    assert text.startswith("Error ") or (isinstance(data, dict) and "error" in data), text[:300]


async def test_create_nonexistent_category_is_graceful(
    live_write_client, call_text, maybe_json
):
    text = await call_text(live_write_client, "create_transaction_rule", {"rule": {
        "merchantNameCriteria": [{"operator": "contains", "value": "MCP-Test-Rule-BadCat"}],
        "setCategoryAction": "000000000000000000",
    }})
    assert "Traceback" not in text, text[:300]
    data = maybe_json(text)
    # Either the server rejects the bad category, or it accepts it — clean up if so.
    if isinstance(data, dict) and data.get("created") is True:
        rules = await call_text(live_write_client, "get_transaction_rules")
        rule_id = _find_rule_id(maybe_json(rules) or [], "MCP-Test-Rule-BadCat")
        if rule_id:
            await live_write_client.call_tool("delete_transaction_rule", {"rule_id": rule_id})
    else:
        assert text.startswith("Error ") or (isinstance(data, dict) and "error" in data), text[:300]


async def test_delete_rule_invalid_id_is_graceful(live_write_client, call_text, maybe_json):
    text = await call_text(
        live_write_client, "delete_transaction_rule", {"rule_id": "000000000000000000"}
    )
    assert "Traceback" not in text, text[:300]
    data = maybe_json(text)
    # Monarch returns "Not found" → decorator yields an "Error ..." string.
    assert text.startswith("Error ") or (isinstance(data, dict) and "error" in data), text[:300]
