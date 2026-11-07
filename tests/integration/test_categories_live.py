"""Live e2e tests for category tools — happy path + live error paths."""
# pylint: disable=missing-function-docstring,redefined-outer-name

import pytest

pytestmark = pytest.mark.integration


async def test_create_category_happy_path_and_cleanup(
    live_write_client, call_text, maybe_json, extract_id, category_group_id
):
    text = await call_text(
        live_write_client, "create_transaction_category",
        {"group_id": category_group_id, "name": "MCP-Test-Category"},
    )
    data = maybe_json(text)
    cat_id = extract_id(data) if data is not None else None
    assert cat_id, f"expected a created category id, got: {text[:300]}"
    deleted = maybe_json(
        await call_text(
            live_write_client, "delete_transaction_category", {"category_id": cat_id}
        )
    )
    assert isinstance(deleted, dict) and deleted.get("deleted") is True
    assert deleted.get("category_id") == cat_id


async def test_create_category_invalid_group_is_graceful(
    live_write_client, call_text, maybe_json, extract_id
):
    text = await call_text(
        live_write_client, "create_transaction_category",
        {"group_id": "invalid-group-id-00000", "name": "MCP-Test-Bad-Group"},
    )
    assert "Traceback" not in text, text[:300]
    data = maybe_json(text)
    cat_id = extract_id(data) if data is not None else None
    if cat_id:
        await live_write_client.call_tool(
            "delete_transaction_category", {"category_id": cat_id}
        )
        pytest.fail("expected an invalid group id to be rejected")
    assert (isinstance(data, dict) and "error" in data) or text.startswith("Error "), text[:300]
