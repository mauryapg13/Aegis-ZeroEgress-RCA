# AGENTS.md

## Project
Zero-egress SRE copilot: a local LLM that root-causes incidents by querying
SigNoz over MCP. No telemetry or prompt ever leaves the host machine/network.
Built for the "Agents of SigNoz" hackathon (Track 01: AI & Agent Observability).

## Tech stack & versions (pin these — do not swap without asking)
- Observability backend: SigNoz self-hosted, Docker Standalone (latest stable
  release per official install script)
- Correlation layer: `signoz-mcp-server` (official SigNoz MCP server), HTTP
  mode on port 8000
- Telemetry source: OpenTelemetry Demo app (astronomy shop), OTLP to
  SigNoz collector on 4317/4318
- Local LLM runtime: Ollama, model = llama3.1:8b-instruct (fallback:
  qwen2.5:7b if tool-calling is flaky or hardware is CPU-only)
- Bridge/glue code: Python 3.11+, official `mcp` client SDK, Ollama's
  OpenAI-compatible `/v1/chat/completions` endpoint for tool calling
- No cloud model, no cloud API key, anywhere in this repo — ever.

## Folder structure
```
/signoz-deploy/       # docker compose / install script for SigNoz + MCP server
/demo-app/            # OTel demo app compose + fault-injection notes
/bridge/              # Python MCP<->Ollama tool-calling bridge (the core deliverable)
/docs/                # README, architecture note, compliance framing (DORA/HIPAA/EU AI Act)
/demo/                # demo script + recorded fallback video
```

## Hard rules
- All telemetry stays inside the local/Docker network. Never add an outbound
  call to any third-party LLM API, even as a "fallback."
- The MCP server already does correlation (traces/logs/metrics/alerts) —
  do not re-implement custom SQL/ClickHouse queries in the bridge. Call MCP
  tools only.
- Every LLM tool call and result must be logged to stdout/file so we can
  visibly prove "zero egress" in the demo.
- Config (SigNoz URL, API key, Ollama host) via environment variables only —
  never hardcoded, never committed.
- Keep the bridge script small and readable (judges will read the code).
  Prefer one clear tool-calling loop over an abstraction layer.
- Write a short test for the tool-calling loop's parsing logic (mock MCP
  response -> confirm the bridge extracts and re-feeds it correctly).
- Ask before touching SigNoz's own config/alerting rules — we rely on
  defaults working out of the box.

## What NOT to do
- Don't build a custom dashboard/UI — SigNoz's own UI is the visual proof;
  a thin chat panel on top is enough.
- Don't add multi-model routing, model switching, or a model picker.
- Don't add user auth, multi-tenant support, or persistence beyond what's
  needed for the demo.
- Don't attempt Kubernetes/Helm deployment — Docker Standalone only, we
  don't have time to debug a cluster today.
- Don't add retry/backoff/production-hardening logic — this is a hackathon
  demo, not a production service. Optimize for "works live, twice."
- Don't scope-creep into a second fault scenario until the first one works
  end-to-end and is recorded as a fallback video.