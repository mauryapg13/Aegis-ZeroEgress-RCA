# SigNoz Deployment & MCP Server Configuration

This folder contains deployment manifests for running self-hosted SigNoz and the official `signoz-mcp-server` via Docker Standalone / Compose.

## Files
* `casting.yaml`: The Foundryctl installation spec that enables SigNoz and the `signoz-mcp` service on port 8000.

## Deploying
To deploy or update the SigNoz stack with MCP enabled:
```bash
foundryctl cast -f ../casting.yaml
```

## Verify MCP Server
```bash
curl -fsS http://localhost:8000/livez && echo " OK"
```
