"""Tests for the --enable-write CLI flag and _WRITE_ENABLED module flag."""

import asyncio
import importlib

import monarch_mcp_server.server as server_module

WRITE_TOOL_NAMES = frozenset({
    "create_transaction", "update_transaction", "delete_transaction",
    "create_transaction_tag", "delete_transaction_tag", "set_transaction_tags",
    "set_budget_amount", "update_transaction_splits",
    "create_transaction_category", "delete_transaction_category",
    "create_manual_account", "update_account", "delete_account",
})


def _resolve_flag(monkeypatch, argv):
    """Re-parse the flag with a custom sys.argv and return the resolved bool."""
    monkeypatch.setattr("sys.argv", argv)
    parsed, _ = server_module._arg_parser.parse_known_args()  # pylint: disable=protected-access
    return parsed.enable_write.lower() in ("true", "1")


class TestEnableWriteFlag:
    """Verify every accepted form of --enable-write."""

    def test_default_no_flag(self, monkeypatch):
        """No flag → False."""
        assert _resolve_flag(monkeypatch, ["server.py"]) is False

    def test_bare_flag(self, monkeypatch):
        """--enable-write (no value) → True."""
        assert _resolve_flag(monkeypatch, ["server.py", "--enable-write"]) is True

    def test_equals_true_lower(self, monkeypatch):
        """--enable-write=true → True."""
        assert _resolve_flag(monkeypatch, ["server.py", "--enable-write=true"]) is True

    def test_equals_true_upper(self, monkeypatch):
        """--enable-write=True (case-insensitive) → True."""
        assert _resolve_flag(monkeypatch, ["server.py", "--enable-write=True"]) is True

    def test_equals_one(self, monkeypatch):
        """--enable-write=1 → True."""
        assert _resolve_flag(monkeypatch, ["server.py", "--enable-write=1"]) is True

    def test_equals_false(self, monkeypatch):
        """--enable-write=false → False."""
        assert _resolve_flag(monkeypatch, ["server.py", "--enable-write=false"]) is False

    def test_equals_zero(self, monkeypatch):
        """--enable-write=0 → False."""
        assert _resolve_flag(monkeypatch, ["server.py", "--enable-write=0"]) is False

    def test_module_level_default(self):
        """Module-level _WRITE_ENABLED is False in test env (no CLI flag)."""
        assert server_module._WRITE_ENABLED is False  # pylint: disable=protected-access

    def test_write_tools_disabled_by_default(self):
        """Write tools are registered with enabled=False when _WRITE_ENABLED is False."""
        all_tools = asyncio.run(server_module.mcp.get_tools())
        for name in WRITE_TOOL_NAMES:
            assert name in all_tools, f"write tool {name!r} not registered"
            assert all_tools[name].enabled is False, (
                f"write tool {name!r} should be disabled by default"
            )
