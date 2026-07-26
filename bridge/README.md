# MCP <-> Local LLM Bridge (Zero-Egress Tool-Calling Loop)

This directory contains the core deliverable for Phase 2: a Python bridge that connects the SigNoz MCP server (`http://localhost:8000/mcp`) to the locally running Ollama Qwen 2.5 3B tool-calling LLM (`http://localhost:11434/v1`).

All telemetry and prompts stay 100% local on the host network.

## Key Design & Security Features
1. **Schema Whitelisting (6 Essential RCA Tools)**: Instead of passing all 41 MCP tools into the local LLM's context window, `mcp_client.py` whitelists precisely 6 tools covering the complete diagnostic chain for Root Cause Analysis:
   - `signoz_list_services` (List services)
   - `signoz_list_alerts` (Check alerts)
   - `signoz_query_metrics` (Query metrics)
   - `signoz_search_traces` (Query traces)
   - `signoz_get_trace_details` (Inspect trace spans)
   - `signoz_search_logs` (Query logs)
2. **Precise Prompt Optimization (91.47% Reduction)**: The full 41-tool schema consumes 188,751 characters (~47,187 tokens). Filtering to our 6 core RCA tools reduces the payload to 16,097 characters (~4,024 tokens), achieving an exact **91.47% reduction** in context bloat for high-speed local inference.
3. **Zero-Egress Security & Audit Logging**: All tool invocations and LLM communications stay entirely on the local network (`localhost`). Every tool execution is recorded with timestamp, duration, payload, and status into `tool_calls.log`.
