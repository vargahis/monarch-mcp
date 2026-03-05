"""Google OAuth authentication flow for Monarch Money."""

import asyncio
from typing import Optional
from urllib.parse import urlparse

from monarch_mcp.secure_session import secure_session

MONARCH_LOGIN_URL = "https://app.monarch.com/login"
MONARCH_ALLOWED_HOST_SUFFIXES = (
    "api.monarch.com",
    "api.monarchmoney.com",
    "monarch.com",
    "monarchmoney.com",
)


def _is_monarch_host(url: str) -> bool:
    """Return True if the request URL points to a Monarch host."""
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return any(
        host == suffix or host.endswith(f".{suffix}")
        for suffix in MONARCH_ALLOWED_HOST_SUFFIXES
    )


async def capture_google_oauth_token(timeout_seconds: int = 300) -> Optional[str]:
    """Open interactive browser login and capture Monarch auth token."""
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Google OAuth requires Playwright. Install with `pip install playwright` "
            "and run `playwright install chromium`."
        ) from exc

    captured_token: Optional[str] = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 "
                "Safari/537.36"
            ),
        )
        page = await context.new_page()

        async def handle_request(request):
            nonlocal captured_token
            if captured_token:
                return

            auth_header = request.headers.get("authorization", "")
            if not auth_header.startswith("Token "):
                return
            if not _is_monarch_host(request.url):
                return

            token = auth_header[6:].strip()
            if token:
                captured_token = token

        page.on("request", handle_request)
        await page.goto(MONARCH_LOGIN_URL)

        deadline = asyncio.get_event_loop().time() + timeout_seconds
        while not captured_token and asyncio.get_event_loop().time() < deadline:
            await asyncio.sleep(1)

        await browser.close()

    return captured_token


def authenticate_with_google_oauth(timeout_seconds: int = 300) -> dict[str, str | bool]:
    """Run Google OAuth flow and persist token into secure keyring storage."""
    token = asyncio.run(capture_google_oauth_token(timeout_seconds=timeout_seconds))
    if not token:
        return {
            "success": False,
            "message": "Timeout: no Monarch auth token captured. Please try again.",
        }

    secure_session.save_token(token)
    return {
        "success": True,
        "message": "Authentication successful. Token saved to secure keyring storage.",
    }
