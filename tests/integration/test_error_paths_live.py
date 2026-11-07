"""Live e2e error-path matrix — invalid ids across tools must fail gracefully.

These exercise the live API + the `_handle_mcp_errors` decorator: the MCP layer
must always return a string (a graceful "Error <op>: ..." or a valid JSON
payload) and never leak an unhandled exception.
"""
# pylint: disable=missing-function-docstring,redefined-outer-name

import pytest

pytestmark = pytest.mark.integration

_BAD = "invalid-id-000000000000"

_CASES = [
    ("update_transaction", {"transaction_id": _BAD, "notes": "MCP-Test"}),
    ("delete_transaction", {"transaction_id": _BAD}),
    ("get_transaction_details", {"transaction_id": _BAD}),
    ("get_transaction_splits", {"transaction_id": _BAD}),
    ("delete_transaction_tag", {"tag_id": _BAD}),
    ("get_account_holdings", {"account_id": _BAD}),
]


@pytest.mark.parametrize("tool,args", _CASES, ids=[c[0] for c in _CASES])
async def test_invalid_id_is_graceful(live_write_client, call_text, maybe_json, tool, args):
    text = await call_text(live_write_client, tool, args)
    assert "Traceback" not in text, text[:300]
    data = maybe_json(text)
    assert data is not None or text.startswith("Error "), \
        f"{tool} did not fail gracefully: {text[:300]}"
