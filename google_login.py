#!/usr/bin/env python3
"""Standalone Google OAuth login script for Monarch MCP."""

import sys
from pathlib import Path

# Add src directory for local development invocation.
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from monarch_mcp.google_oauth import authenticate_with_google_oauth


def main() -> int:
    """Run interactive Google OAuth and store token in keyring."""
    print("\nMonarch Money - Google OAuth Login")
    print("=" * 40)
    print("A browser window will open.")
    print("1. Click 'Sign in with Google'")
    print("2. Complete authentication")
    print("3. Wait for Monarch app to load\n")

    result = authenticate_with_google_oauth()
    print(result["message"])
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
