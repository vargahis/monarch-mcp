# Authentication Architecture

Technical details on how the Monarch MCP Server handles authentication, session management, and security.

## Authentication Flow

1. On startup the server checks for a token in the system keyring
2. If no token is found, a local HTTP server is started on a random port and the browser is opened to a login page
3. The user signs in (with MFA if enabled); the token is saved to the keyring
4. The temporary auth server shuts down automatically
5. If a token later expires, the same flow is re-triggered on the next tool call

## Session Management

- Tokens are stored securely in the system keyring (service: `com.mcp.monarch-mcp-server`)
- The monarchmoneycommunity library hardwires `trusted_device=True`, which produces long-lived tokens that last weeks to months
- Sessions persist across Claude Desktop restarts
- Expired tokens are detected automatically and cleared, triggering re-authentication

## Security

- Credentials are entered in your local browser, never transmitted through Claude Desktop
- The auth server binds to `127.0.0.1` only (not accessible from the network)
- MFA/2FA fully supported
- Token stored in the OS keyring, not in plain-text files

## Fallback: CLI Login

For headless environments where a browser is not available, run:

```bash
python login_setup.py
```

This authenticates interactively in the terminal and stores the token in the same keyring location.
