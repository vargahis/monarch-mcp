"""Monarch Money MCP Server - Main server implementation."""

import functools
import json
import logging
import os
import re
import traceback
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from gql import gql
from gql.transport.exceptions import TransportServerError, TransportQueryError, TransportError
from monarchmoney import MonarchMoney, LoginFailedException

from monarch_mcp_server.secure_session import secure_session, is_auth_error
from monarch_mcp_server.auth_server import trigger_auth_flow, _run_sync

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Monarch Money MCP Server")


def run_async(coro):
    """Run async function in a new thread with its own event loop.

    If the coroutine raises an authentication error (expired token,
    invalid credentials), the stale token is cleared from the keyring,
    the browser-based auth flow is re-triggered, and a RuntimeError is
    raised so the calling tool can inform the user.

    Only catches the two exception types that ``is_auth_error`` can
    recognise; everything else propagates unchanged to the caller.
    """
    with ThreadPoolExecutor() as executor:
        future = executor.submit(_run_sync, coro)
        try:
            return future.result()
        except (TransportServerError, LoginFailedException) as exc:
            if is_auth_error(exc):
                logger.warning("Token appears expired — clearing and triggering re-auth")
                secure_session.delete_token()
                trigger_auth_flow()
                raise RuntimeError(
                    "Your session has expired. A login page has been opened in "
                    "your browser — please sign in and try again."
                ) from exc
            raise


# ── MCP tool error handling ────────────────────────────────────────────

def _handle_mcp_errors(operation: str):
    """Decorator providing granular exception handling for MCP tool functions.

    Catches specific known exception types with appropriate log messages,
    with a catch-all for anything unexpected.  Every path returns a
    user-readable error string so the MCP tool never crashes.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RuntimeError as exc:
                logger.error("Runtime error %s: %s", operation, exc)
                return f"Error {operation}: {exc}"
            except TransportServerError as exc:
                code = getattr(exc, "code", "unknown")
                logger.error(
                    "Monarch API HTTP %s error %s: %s", code, operation, exc,
                )
                return f"Error {operation}: Monarch API returned HTTP {code}: {exc}"
            except TransportQueryError as exc:
                logger.error("Monarch API query error %s: %s", operation, exc)
                return f"Error {operation}: API query failed: {exc}"
            except TransportError as exc:
                logger.error(
                    "Monarch API connection error %s: %s", operation, exc,
                )
                return f"Error {operation}: connection error: {exc}"
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.error(
                    "Unexpected error %s: %s (%s)",
                    operation, exc, type(exc).__name__,
                )
                return f"Error {operation}: {exc}"
        return wrapper
    return decorator


# ── Client helpers ─────────────────────────────────────────────────────

async def get_monarch_client() -> MonarchMoney:
    """Get or create MonarchMoney client instance using secure session storage."""
    # Try to get authenticated client from secure session
    client = secure_session.get_authenticated_client()

    if client is not None:
        logger.info("Using authenticated client from secure keyring storage")
        return client

    # If no secure session, try environment credentials
    email = os.getenv("MONARCH_EMAIL")
    password = os.getenv("MONARCH_PASSWORD")

    if email and password:
        try:
            client = MonarchMoney()
            await client.login(email, password)
            logger.info(
                "Successfully logged into Monarch Money with environment credentials"
            )

            # Save the session securely
            secure_session.save_authenticated_session(client)

            return client
        except Exception as e:
            logger.error("Failed to login to Monarch Money: %s", e)
            raise

    # No credentials anywhere — open browser login and tell the user
    trigger_auth_flow()
    raise RuntimeError(
        "Authentication needed! A login page has been opened in your "
        "browser — please sign in and try again."
    )


# ── Tools ──────────────────────────────────────────────────────────────

@mcp.tool()
def setup_authentication() -> str:
    """Get instructions for setting up secure authentication with Monarch Money."""
    return """Monarch Money - Authentication

Authentication happens automatically in your browser:

1. When the MCP server starts without a saved session, a login page
   opens in your browser automatically

2. Enter your Monarch Money email and password

3. Provide your 2FA code if you have MFA enabled

4. Once authenticated, the token is saved to your system keyring

Then start using Monarch tools in Claude Desktop:
   - get_accounts - View all accounts
   - get_transactions - Recent transactions
   - get_budgets - Budget information

Session persists across Claude restarts (weeks/months).
Expired sessions are re-authenticated automatically.
Credentials are entered in your browser, never through Claude.

Alternative: run `python login_setup.py` in a terminal for
headless environments where a browser is not available."""


@mcp.tool()
def check_auth_status() -> str:
    """Check if already authenticated with Monarch Money."""
    try:
        # Check if we have a token in the keyring
        token = secure_session.load_token()
        if token:
            status = "Authentication token found in secure keyring storage\n"
        else:
            status = "No authentication token found in keyring\n"

        email = os.getenv("MONARCH_EMAIL")
        if email:
            status += f"Environment email: {email}\n"

        status += (
            "\nTry get_accounts to test connection or run login_setup.py if needed."
        )

        return status
    except Exception as e:  # pylint: disable=broad-exception-caught
        return f"Error checking auth status: {e}"


@mcp.tool()
def debug_session_loading() -> str:
    """Debug keyring session loading issues."""
    try:
        # Check keyring access
        token = secure_session.load_token()
        if token:
            return f"Token found in keyring (length: {len(token)})"
        return "No token found in keyring. Run login_setup.py to authenticate."
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_details = traceback.format_exc()
        return (
            f"Keyring access failed:\nError: {e}\n"
            f"Type: {type(e)}\nTraceback:\n{error_details}"
        )


@mcp.tool()
@_handle_mcp_errors("getting accounts")
def get_accounts() -> str:
    """Get all financial accounts from Monarch Money."""

    async def _get_accounts():
        client = await get_monarch_client()
        return await client.get_accounts()

    accounts = run_async(_get_accounts())

    # Format accounts for display
    account_list = []
    for account in accounts.get("accounts", []):
        account_info = {
            "id": account.get("id"),
            "name": account.get("displayName") or account.get("name"),
            "type": (account.get("type") or {}).get("name"),
            "balance": account.get("currentBalance"),
            "institution": (account.get("institution") or {}).get("name"),
            "is_active": account.get("isActive")
            if "isActive" in account
            else not account.get("deactivatedAt"),
        }
        account_list.append(account_info)

    return json.dumps(account_list, indent=2, default=str)


@mcp.tool()
@_handle_mcp_errors("getting transactions")
def get_transactions(
    limit: int = 100,
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account_id: Optional[str] = None,
) -> str:
    """
    Get transactions from Monarch Money.

    Args:
        limit: Number of transactions to retrieve (default: 100)
        offset: Number of transactions to skip (default: 0)
        start_date: Start date in YYYY-MM-DD format (requires end_date)
        end_date: End date in YYYY-MM-DD format (requires start_date)
        account_id: Specific account ID to filter by
    """
    if bool(start_date) != bool(end_date):
        return json.dumps(
            {"error": "Both start_date and end_date are required when filtering by date."},
            indent=2,
        )

    async def _get_transactions():
        client = await get_monarch_client()

        filters = {}
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        if account_id:
            filters["account_ids"] = [account_id]

        return await client.get_transactions(limit=limit, offset=offset, **filters)

    transactions = run_async(_get_transactions())

    # Format transactions for display
    transaction_list = []
    for txn in transactions.get("allTransactions", {}).get("results", []):
        transaction_info = {
            "id": txn.get("id"),
            "date": txn.get("date"),
            "amount": txn.get("amount"),
            "original_name": txn.get("plaidName"),
            "category": txn.get("category", {}).get("name")
            if txn.get("category")
            else None,
            "account": txn.get("account", {}).get("displayName"),
            "merchant": txn.get("merchant", {}).get("name")
            if txn.get("merchant")
            else None,
            "notes": txn.get("notes"),
            "is_pending": txn.get("pending", False),
            "is_recurring": txn.get("isRecurring", False),
            "tags": [
                {
                    "id": tag.get("id"),
                    "name": tag.get("name"),
                    "color": tag.get("color"),
                }
                for tag in txn.get("tags", [])
            ],
        }
        transaction_list.append(transaction_info)

    return json.dumps(transaction_list, indent=2, default=str)


@mcp.tool()
@_handle_mcp_errors("getting budgets")
def get_budgets(
    start_date: Optional[str] = None, end_date: Optional[str] = None
) -> str:
    """
    Get budget information from Monarch Money.

    Args:
        start_date: Start date in YYYY-MM-DD format (default: last month)
        end_date: End date in YYYY-MM-DD format (default: next month)
    """
    if bool(start_date) != bool(end_date):
        return json.dumps(
            {"error": "Both start_date and end_date are required when filtering by date."},
            indent=2,
        )

    async def _get_budgets():
        client = await get_monarch_client()
        filters = {}
        if start_date is not None:
            filters["start_date"] = start_date
        if end_date is not None:
            filters["end_date"] = end_date
        return await client.get_budgets(**filters)

    budgets = run_async(_get_budgets())

    return json.dumps(budgets, indent=2, default=str)


@mcp.tool()
@_handle_mcp_errors("getting cashflow")
def get_cashflow(
    start_date: Optional[str] = None, end_date: Optional[str] = None
) -> str:
    """
    Get cashflow analysis from Monarch Money.

    Args:
        start_date: Start date in YYYY-MM-DD format (requires end_date; defaults to current month)
        end_date: End date in YYYY-MM-DD format (requires start_date; defaults to current month)
    """
    if bool(start_date) != bool(end_date):
        return json.dumps(
            {"error": "Both start_date and end_date are required when filtering by date."},
            indent=2,
        )

    async def _get_cashflow():
        client = await get_monarch_client()

        filters = {}
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date

        return await client.get_cashflow(**filters)

    cashflow = run_async(_get_cashflow())

    return json.dumps(cashflow, indent=2, default=str)


@mcp.tool()
@_handle_mcp_errors("getting account holdings")
def get_account_holdings(account_id: str) -> str:
    """
    Get investment holdings for a specific account.

    Args:
        account_id: The ID of the investment account
    """

    async def _get_holdings():
        client = await get_monarch_client()
        return await client.get_account_holdings(account_id)

    holdings = run_async(_get_holdings())

    return json.dumps(holdings, indent=2, default=str)


@mcp.tool()
@_handle_mcp_errors("creating transaction")
def create_transaction(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    account_id: str,
    amount: float,
    merchant_name: str,
    category_id: str,
    date: str,
    notes: Optional[str] = None,
) -> str:
    """
    Create a new transaction in Monarch Money.

    Args:
        account_id: The account ID to add the transaction to
        amount: Transaction amount (positive for income, negative for expenses)
        merchant_name: Merchant name for the transaction
        category_id: Category ID for the transaction
        date: Transaction date in YYYY-MM-DD format
        notes: Optional transaction notes
    """

    async def _create_transaction():
        client = await get_monarch_client()
        return await client.create_transaction(
            date=date,
            account_id=account_id,
            amount=amount,
            merchant_name=merchant_name,
            category_id=category_id,
            notes=notes or "",
        )

    result = run_async(_create_transaction())

    return json.dumps(result, indent=2, default=str)


@mcp.tool()
@_handle_mcp_errors("updating transaction")
def update_transaction(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    transaction_id: str,
    category_id: Optional[str] = None,
    merchant_name: Optional[str] = None,
    goal_id: Optional[str] = None,
    amount: Optional[float] = None,
    date: Optional[str] = None,
    hide_from_reports: Optional[bool] = None,
    needs_review: Optional[bool] = None,
    notes: Optional[str] = None,
) -> str:
    """
    Update an existing transaction in Monarch Money.

    Args:
        transaction_id: The ID of the transaction to update
        category_id: New category ID
        merchant_name: New merchant name
        goal_id: Goal ID to associate with the transaction
        amount: New transaction amount
        date: New transaction date in YYYY-MM-DD format
        hide_from_reports: Whether to hide the transaction from reports
        needs_review: Whether the transaction needs review
        notes: Transaction notes
    """

    async def _update_transaction():
        client = await get_monarch_client()

        update_data = {"transaction_id": transaction_id}

        if category_id is not None:
            update_data["category_id"] = category_id
        if merchant_name is not None:
            update_data["merchant_name"] = merchant_name
        if goal_id is not None:
            update_data["goal_id"] = goal_id
        if amount is not None:
            update_data["amount"] = amount
        if date is not None:
            update_data["date"] = date
        if hide_from_reports is not None:
            update_data["hide_from_reports"] = hide_from_reports
        if needs_review is not None:
            update_data["needs_review"] = needs_review
        if notes is not None:
            update_data["notes"] = notes

        return await client.update_transaction(**update_data)

    result = run_async(_update_transaction())

    return json.dumps(result, indent=2, default=str)


@mcp.tool()
@_handle_mcp_errors("deleting transaction")
def delete_transaction(transaction_id: str) -> str:
    """
    Delete a transaction from Monarch Money.

    Args:
        transaction_id: The ID of the transaction to delete
    """

    async def _delete_transaction():
        client = await get_monarch_client()
        return await client.delete_transaction(transaction_id)

    run_async(_delete_transaction())

    return json.dumps({"deleted": True, "transaction_id": transaction_id}, indent=2)


@mcp.tool()
@_handle_mcp_errors("refreshing accounts")
def refresh_accounts() -> str:
    """Request account data refresh from financial institutions."""

    async def _refresh_accounts():
        client = await get_monarch_client()
        accounts = await client.get_accounts()
        account_ids = [
            account["id"]
            for account in accounts.get("accounts", [])
            if account.get("id")
        ]
        if not account_ids:
            return {"error": "No accounts found to refresh."}
        return await client.request_accounts_refresh(account_ids)

    result = run_async(_refresh_accounts())

    return json.dumps(result, indent=2, default=str)


@mcp.tool()
@_handle_mcp_errors("getting transaction tags")
def get_transaction_tags() -> str:
    """Get all transaction tags from Monarch Money."""

    async def _get_transaction_tags():
        client = await get_monarch_client()
        return await client.get_transaction_tags()

    tags = run_async(_get_transaction_tags())

    # Format tags for display
    tag_list = []
    for tag in tags.get("householdTransactionTags", []):
        tag_info = {
            "id": tag.get("id"),
            "name": tag.get("name"),
            "color": tag.get("color"),
            "order": tag.get("order"),
            "transactionCount": tag.get("transactionCount"),
        }
        tag_list.append(tag_info)

    return json.dumps(tag_list, indent=2, default=str)


@mcp.tool()
@_handle_mcp_errors("creating transaction tag")
def create_transaction_tag(name: str, color: str) -> str:
    """
    Create a new transaction tag in Monarch Money.

    Args:
        name: Tag name (required)
        color: Hex RGB color including # (required, e.g., "#19D2A5")
    """
    # Validate color format
    if not re.match(r"^#[0-9A-Fa-f]{6}$", color):
        return json.dumps(
            {
                "error": "Invalid color format. Use hex RGB with # (e.g., '#19D2A5')"
            },
            indent=2,
        )

    # Validate name
    if not name or not name.strip():
        return json.dumps({"error": "Tag name cannot be empty"}, indent=2)

    async def _create_transaction_tag():
        client = await get_monarch_client()
        return await client.create_transaction_tag(name, color)

    result = run_async(_create_transaction_tag())

    return json.dumps(result, indent=2, default=str)


@mcp.tool()
@_handle_mcp_errors("deleting transaction tag")
def delete_transaction_tag(tag_id: str) -> str:
    """
    Delete a transaction tag from Monarch Money.

    Args:
        tag_id: The ID of the tag to delete
    """

    async def _delete_transaction_tag():
        client = await get_monarch_client()
        mutation = gql(
            """
            mutation Common_DeleteTransactionTag($tagId: ID!) {
                deleteTransactionTag(tagId: $tagId) {
                    __typename
                }
            }
            """
        )
        variables = {"tagId": tag_id}
        return await client.gql_call(
            operation="Common_DeleteTransactionTag",
            graphql_query=mutation,
            variables=variables,
        )

    run_async(_delete_transaction_tag())

    return json.dumps({"deleted": True, "tag_id": tag_id}, indent=2)


@mcp.tool()
@_handle_mcp_errors("setting transaction tags")
def set_transaction_tags(transaction_id: str, tag_ids: List[str]) -> str:
    """
    Set tags on a transaction (replaces existing tags).

    Args:
        transaction_id: Transaction UUID (required)
        tag_ids: List of tag IDs to apply (required, empty list removes all tags)

    Note: This overwrites existing tags. To remove all tags, pass an empty list.
    """

    async def _set_transaction_tags():
        client = await get_monarch_client()
        return await client.set_transaction_tags(transaction_id, tag_ids)

    result = run_async(_set_transaction_tags())

    return json.dumps(result, indent=2, default=str)


def main():
    """Main entry point for the server."""
    logger.info("Starting Monarch Money MCP Server...")

    # Auto-trigger browser authentication if no credentials are available
    trigger_auth_flow()

    try:
        mcp.run()
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to run server: %s", e)
        raise


# Export for mcp run
app = mcp

if __name__ == "__main__":
    main()
