# Authentication Architecture

Technical details on how the Monarch MCP Server handles authentication, session management, and security.

## Authentication Flow

1. On startup the server checks for credentials in the configured keyring
2. If none are found, a local HTTP server is started on a random port and the browser is opened to a login page
3. The user signs in (with MFA if enabled); the token is saved to the keyring
4. The temporary auth server shuts down automatically
5. If credentials later expire, the same flow is re-triggered on the next tool call

## Session Management

- Tokens or browser cookies are stored in the configured keyring (service: `com.mcp.monarch-mcp`)
- The monarchmoneycommunity library hardwires `trusted_device=True`, which produces long-lived tokens that last weeks to months
- Sessions persist across Claude Desktop restarts
- Expired tokens are detected automatically and cleared, triggering re-authentication

## Security

- Credentials are entered in your local browser, never transmitted through Claude Desktop
- The auth server binds to `127.0.0.1` only (not accessible from the network)
- MFA/2FA fully supported
- A secure OS keyring protects credentials at rest. The optional
  `keyrings.alt.file.PlaintextKeyring` stores them unencrypted and should be
  used only when the risks of a readable file are acceptable.

## Fallback: CLI Login

For headless environments where a browser is not available, run:

```bash
python login_setup.py
```

This authenticates interactively in the terminal and stores the token in the same keyring location.
