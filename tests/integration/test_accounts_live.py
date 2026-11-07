"""Live e2e tests for account-management tools — lifecycle + live error paths."""
# pylint: disable=missing-function-docstring,redefined-outer-name

import pytest

pytestmark = pytest.mark.integration


def _pick_type_subtype(options):
    """Extract a usable (type, subtype) name pair from get_account_type_options."""
    items = options.get("accountTypeOptions") if isinstance(options, dict) else None
    if not items and isinstance(options, dict):
        for value in options.values():
            if isinstance(value, list):
                items = value
                break
    for opt in items or []:
        if not isinstance(opt, dict):
            continue
        type_name = (opt.get("type") or {}).get("name")
        subs = opt.get("subtypes")
        if not subs and opt.get("subtype"):
            subs = [opt["subtype"]]
        for sub in subs or []:
            sub_name = (sub or {}).get("name")
            if type_name and sub_name:
                return type_name, sub_name
    return None, None


@pytest.fixture
async def account_type_subtype(live_write_client, call_json):
    options = await call_json(live_write_client, "get_account_type_options")
    type_name, sub_name = _pick_type_subtype(options)
    if not (type_name and sub_name):
        pytest.skip("could not discover a valid account type/subtype from the live account")
    return type_name, sub_name


async def test_account_create_update_delete_lifecycle(
    live_write_client, call_text, maybe_json, extract_id, account_type_subtype
):
    type_name, sub_name = account_type_subtype
    created = maybe_json(
        await call_text(
            live_write_client, "create_manual_account",
            {
                "account_name": "MCP-Test-Account",
                "account_type": type_name,
                "account_sub_type": sub_name,
                "is_in_net_worth": False,
                "account_balance": 0,
            },
        )
    )
    account_id = extract_id(created) if created is not None else None
    assert account_id, f"expected a created account id, got: {created}"
    try:
        renamed = await call_text(
            live_write_client, "update_account",
            {"account_id": account_id, "account_name": "MCP-Test-Renamed"},
        )
        assert "Traceback" not in renamed, renamed[:300]
    finally:
        deleted = maybe_json(
            await call_text(
                live_write_client, "delete_account", {"account_id": account_id}
            )
        )
        assert isinstance(deleted, dict) and deleted.get("deleted") is True
        assert deleted.get("account_id") == account_id


@pytest.mark.parametrize("tool", ["update_account", "delete_account"])
async def test_account_invalid_id_is_graceful(live_write_client, call_text, maybe_json, tool):
    args = {"account_id": "invalid-account-id-00000"}
    if tool == "update_account":
        args["account_name"] = "MCP-Test-Nope"
    text = await call_text(live_write_client, tool, args)
    assert "Traceback" not in text, text[:300]
    data = maybe_json(text)
    assert data is not None or text.startswith("Error "), text[:300]
