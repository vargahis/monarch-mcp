"""Live e2e tests for transaction-tag tools — robustness + live error paths.

(Color-format and empty-name validation happen in our Python layer before any
API call and are covered deterministically by tests/test_tag_crud.py, so they
are intentionally not duplicated here.)
"""
# pylint: disable=missing-function-docstring,redefined-outer-name

import pytest

pytestmark = pytest.mark.integration


async def _create_or_graceful(client, call_text, maybe_json, extract_id, name, color="#FF5733"):
    """Create a tag; if it succeeds, delete it. Assert the MCP layer never crashes."""
    text = await call_text(client, "create_transaction_tag", {"name": name, "color": color})
    assert "Traceback" not in text, text[:300]
    data = maybe_json(text)
    tag_id = extract_id(data) if data is not None else None
    if tag_id:
        await client.call_tool("delete_transaction_tag", {"tag_id": tag_id})
        return "created"
    assert (isinstance(data, dict) and "error" in data) or text.startswith("Error "), \
        f"expected created tag or graceful error, got: {text[:300]}"
    return "error"


async def test_create_tag_happy_path_and_cleanup(
    live_write_client, call_text, maybe_json, extract_id
):
    text = await call_text(
        live_write_client, "create_transaction_tag",
        {"name": "MCP-Test-Tag", "color": "#FF5733"},
    )
    data = maybe_json(text)
    tag_id = extract_id(data) if data is not None else None
    assert tag_id, f"expected a created tag id, got: {text[:300]}"
    deleted = maybe_json(
        await call_text(live_write_client, "delete_transaction_tag", {"tag_id": tag_id})
    )
    assert deleted == {"deleted": True, "tag_id": tag_id}


@pytest.mark.parametrize(
    "name",
    [
        "MCP-Test-テスト-🏷️",                       # unicode
        "MCP-Test-LongName-" + "A" * 200,            # 200+ chars
        "MCP-Test-&'\"<>",                            # special characters
    ],
)
async def test_create_tag_adversarial_name_is_graceful(
    live_write_client, call_text, maybe_json, extract_id, name
):
    await _create_or_graceful(live_write_client, call_text, maybe_json, extract_id, name)
