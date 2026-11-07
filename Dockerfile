# Dev image for the cookie-auth fork of vargahis/monarch-mcp.
#
# Installs THIS local (modified) MCP — its pyproject pins monarchmoneycommunity
# to the #41 cookie-auth branch — plus mcp-proxy (stdio->SSE bridge) and a
# headless file keyring. Read-only by default (no --enable-write).
#
# Seed cookie auth once, then serve:
#   docker run --rm -e MONARCH_COOKIE='session_id=...; csrftoken=...' \
#     -v monarch-token:/data --entrypoint python <image> cookie_login.py
FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir mcp-proxy keyrings.alt

# Build the local MCP (pulls the #41 cookie-auth lib branch via pyproject).
COPY . /app/monarch-mcp
WORKDIR /app/monarch-mcp
RUN pip install --no-cache-dir .

# Headless keyring on the mounted /data volume (no OS keychain in a container).
ENV KEYRING_BACKEND=keyrings.alt.file.PlaintextKeyring
ENV XDG_DATA_HOME=/data
ENV HOME=/data

EXPOSE 7012

# Serve: mcp-proxy runs the read-only `monarch-mcp` stdio server, exposed as SSE.
CMD ["mcp-proxy", "--pass-environment", "--host", "0.0.0.0", "--port", "7012", "--named-server-config", "/config/servers.json"]
