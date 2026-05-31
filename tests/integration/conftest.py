"""Fixtures for the live end-to-end (e2e) integration suite.

These tests hit a **real** Monarch Money account. They verify that the MCP
*tools* behave robustly against the live API (adversarial/edge inputs, live
error paths) — distinct from the mocked unit tests (`tests/`, which never hit
the network) and from the `test-monarch-mcp` agent skill (which checks that the
*AI agent* calls the tools correctly).

Safety / gating:

* Deselected by default via ``addopts = -m 'not integration'`` (pyproject.toml).
  Run them explicitly with ``MONARCH_LIVE_TESTS=1 pytest tests/integration -m integration``.
* ``live_client`` additionally skips unless ``MONARCH_LIVE_TESTS=1`` and a
  credential source exists (a keyring token via ``login_setup.py``, or
  ``MONARCH_EMAIL`` / ``MONARCH_PASSWORD``).
* This conftest deliberately **overrides** the mocked autouse ``_isolate`` from
  ``tests/conftest.py`` so tools reach the real API, and it **neuters** the
  credential-destroying recovery paths (``delete_token`` / ``trigger_auth_flow``)
  so a live 401/403/WAF response can never wipe the user's keyring session.
"""
# pylint: disable=missing-function-docstring,redefined-outer-name

import asyncio
import json
import os
from unittest.mock import patch

import pytest
from fastmcp import Client
from monarchmoney import MonarchMoney

from monarch_mcp.server import mcp
from monarch_mcp.secure_session import secure_session

RUN_LIVE = os.getenv("MONARCH_LIVE_TESTS") == "1"
TEST_PREFIX = "MCP-Test-"


# ── helpers (also exposed as fixtures further down) ────────────────────

async def _call_json(client, name, args=None):
    """Call an MCP tool through the client and parse its JSON text payload."""
    result = await client.call_tool(name, args or {})
    return json.loads(result.content[0].text)


async def _call_text(client, name, args=None):
    """Call an MCP tool and return its raw text payload (for error-path checks)."""
    result = await client.call_tool(name, args or {})
    return result.content[0].text


def _extract_id(obj):
    """Depth-first search for the first ``id`` in a Monarch mutation payload.

    Create mutations nest the new object one or two levels deep
    (e.g. ``createTransaction.transaction.id``); it is the only object carrying
    an ``id``, so the first match is the resource we just created.
    """
    if isinstance(obj, dict):
        if isinstance(obj.get("id"), str):
            return obj["id"]
        for value in obj.values():
            found = _extract_id(value)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _extract_id(item)
            if found:
                return found
    return None


def _parse(text):
    """Parse a tool response: dict/list for JSON, or None for a bare error string.

    In-tool validation errors are ``json.dumps({"error": ...})`` (valid JSON);
    decorator-level exceptions return a bare ``"Error <op>: ..."`` string.
    """
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None


def _noop(*_args, **_kwargs):
    return None


def _enable_write_tools(tools):
    """Enable every currently-disabled (write-gated) tool; return the flipped list."""
    flipped = []
    for tool in tools.values():
        if not tool.enabled:
            tool.enabled = True
            flipped.append(tool)
    return flipped


# ── real authenticated client (session-scoped, sync) ───────────────────

@pytest.fixture(scope="session")
def live_client():
    if not RUN_LIVE:
        pytest.skip("live e2e disabled — set MONARCH_LIVE_TESTS=1 to enable")

    client = secure_session.get_authenticated_client()
    if client is not None:
        return client

    email = os.getenv("MONARCH_EMAIL")
    password = os.getenv("MONARCH_PASSWORD")
    if not (email and password):
        pytest.skip(
            "no live Monarch credentials — run login_setup.py to store a keyring "
            "token, or set MONARCH_EMAIL / MONARCH_PASSWORD"
        )

    client = MonarchMoney()
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(client.login(email, password))
    finally:
        loop.close()
    return client


# ── override the mocked autouse _isolate from tests/conftest.py ────────

@pytest.fixture(autouse=True)
def _isolate(live_client, monkeypatch):  # noqa: F811
    """Inject the real client and disarm the credential-destroying auth paths."""
    async def _real_client():
        return live_client

    monkeypatch.setattr("monarch_mcp.server._get_monarch_client", _real_client)
    monkeypatch.setattr("monarch_mcp.server.trigger_auth_flow", _noop)
    monkeypatch.setattr("monarch_mcp.auth_server.trigger_auth_flow", _noop)
    monkeypatch.setattr(secure_session, "delete_token", _noop)
    yield


# ── MCP clients ────────────────────────────────────────────────────────

@pytest.fixture
async def live_mcp_client():
    """Read-only client (write tools stay disabled)."""
    async with Client(mcp) as client:
        yield client


@pytest.fixture
async def live_write_client():
    """Client with write tools enabled, backed by the real Monarch client."""
    tools = await mcp.get_tools()
    flipped = _enable_write_tools(tools)
    try:
        async with Client(mcp) as client:
            yield client
    finally:
        for tool in flipped:
            tool.enabled = False


# ── discovery values (function-scoped; small suite, so re-fetch is fine) ─

@pytest.fixture
async def checking_account_id(live_write_client):
    accounts = await _call_json(live_write_client, "get_accounts")
    assert accounts, "live account has no accounts to test against"
    for acct in accounts:
        if "checking" in (acct.get("type") or "").lower():
            return acct["id"]
    return accounts[0]["id"]


@pytest.fixture
async def category_id(live_write_client):
    cats = await _call_json(live_write_client, "get_transaction_categories")
    pool = [c for c in cats if not c.get("is_disabled")] or cats
    assert pool, "live account has no transaction categories"
    return pool[0]["id"]


@pytest.fixture
async def category_group_id(live_write_client):
    groups = await _call_json(live_write_client, "get_transaction_category_groups")
    candidates = groups.get("categoryGroups") if isinstance(groups, dict) else None
    if not candidates and isinstance(groups, dict):
        for value in groups.values():
            if (isinstance(value, list) and value
                    and isinstance(value[0], dict) and value[0].get("id")):
                candidates = value
                break
    assert candidates, "live account has no category groups"
    return candidates[0]["id"]


@pytest.fixture
async def second_category_id(live_write_client, category_id):
    """A different category id than ``category_id`` (for split-rule legs)."""
    cats = await _call_json(live_write_client, "get_transaction_categories")
    pool = [c for c in cats if not c.get("is_disabled")] or cats
    for cat in pool:
        if cat["id"] != category_id:
            return cat["id"]
    return category_id


@pytest.fixture
async def tag_id(live_write_client):
    """Create an MCP-Test- tag for rule-action tests; delete it on teardown."""
    result = await _call_json(
        live_write_client, "create_transaction_tag",
        {"name": "MCP-Test-Rule-Tag", "color": "#19D2A5"},
    )
    new_id = _extract_id(result)
    assert new_id, f"could not create a tag for rule tests: {result}"
    try:
        yield new_id
    finally:
        await live_write_client.call_tool("delete_transaction_tag", {"tag_id": new_id})


# ── callable helpers exposed to tests ──────────────────────────────────

@pytest.fixture
def call_json():
    return _call_json


@pytest.fixture
def call_text():
    return _call_text


@pytest.fixture
def extract_id():
    return _extract_id


@pytest.fixture
def maybe_json():
    return _parse


# ── self-cleaning backstop ─────────────────────────────────────────────

async def _sweep(client):
    """Delete every MCP-Test- resource reachable through the MCP tools."""
    tags = await _call_json(client, "get_transaction_tags")
    for tag in tags:
        if (tag.get("name") or "").startswith(TEST_PREFIX):
            await client.call_tool("delete_transaction_tag", {"tag_id": tag["id"]})

    txns = await _call_json(client, "get_transactions", {"search": "MCP-Test", "limit": 100})
    for txn in txns:
        await client.call_tool("delete_transaction", {"transaction_id": txn["id"]})

    cats = await _call_json(client, "get_transaction_categories")
    for cat in cats:
        if (cat.get("name") or "").startswith(TEST_PREFIX):
            await client.call_tool("delete_transaction_category", {"category_id": cat["id"]})

    accounts = await _call_json(client, "get_accounts")
    for acct in accounts:
        if (acct.get("name") or "").startswith(TEST_PREFIX):
            await client.call_tool("delete_account", {"account_id": acct["id"]})

    # Monarch lowercases rule criteria, so test rules read as "mcp-test".
    rules = await _call_json(client, "get_transaction_rules")
    for rule in rules:
        values = [c.get("value", "") for c in (rule.get("merchant_name_criteria") or [])]
        values += [c.get("value", "") for c in (rule.get("original_statement_criteria") or [])]
        if any("mcp-test" in (v or "").lower() for v in values):
            await client.call_tool("delete_transaction_rule", {"rule_id": rule["id"]})


@pytest.fixture(scope="session", autouse=True)
def _final_sweep(live_client):
    """After the whole suite, delete any MCP-Test- residue left by a crashed test."""
    yield
    if not RUN_LIVE or live_client is None:
        return

    async def _run():
        async def _real_client():
            return live_client
        with (
            patch("monarch_mcp.server._get_monarch_client", _real_client),
            patch("monarch_mcp.server.trigger_auth_flow", _noop),
            patch("monarch_mcp.auth_server.trigger_auth_flow", _noop),
            patch.object(secure_session, "delete_token", _noop),
        ):
            tools = await mcp.get_tools()
            flipped = _enable_write_tools(tools)
            try:
                async with Client(mcp) as client:
                    await _sweep(client)
            finally:
                for tool in flipped:
                    tool.enabled = False

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run())
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # Best-effort backstop — never fail the session on a sweep error.
        print(f"[final-sweep] warning: cleanup sweep failed: {exc}")
    finally:
        loop.close()
