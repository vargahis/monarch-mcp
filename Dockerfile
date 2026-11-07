# Dev image for the cookie-auth fork of vargahis/monarch-mcp.
#
# Installs THIS local (modified) MCP — monarchmoneycommunity>=1.7 provides
# cookie/CSRF auth — plus mcp-proxy (stdio->SSE bridge) and a
# headless file keyring. Read-only by default (no --enable-write).
#
# No keyring is enabled by default. Configure a secure backend, or explicitly
# opt into keyrings.alt.file.PlaintextKeyring for local use. Its /data volume
# stores reusable cookies unencrypted and must be protected accordingly.
FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "mcp-proxy~=0.14.0" keyrings.alt

# Build the local MCP.
COPY . /app/monarch-mcp
WORKDIR /app/monarch-mcp
RUN pip install --no-cache-dir .

# Require an explicit keyring choice in headless containers.
ENV PYTHON_KEYRING_BACKEND=keyring.backends.fail.Keyring
ENV XDG_DATA_HOME=/data
ENV HOME=/data

EXPOSE 7012

# Serve: mcp-proxy runs the read-only `monarch-mcp` stdio server, exposed as SSE.
# mcp-proxy >=0.14 rejects unknown Host headers (DNS-rebinding guard, HTTP 421);
# trust the compose service name the gateways use.
CMD ["mcp-proxy", "--pass-environment", "--host", "0.0.0.0", "--port", "7012", \
     "--allowed-host", "monarch-money-mcp", "--allowed-host", "monarch-money-mcp:7012", \
     "--named-server-config", "/config/servers.json"]
