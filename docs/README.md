# Zero-Egress SRE Copilot: Architecture & Compliance

## Overview
This architecture ensures zero egress of telemetry data or prompt context, making it ideal for regulated industries (banks, healthcare, government, DORA, HIPAA, EU AI Act compliance).

## Architecture
1. **Telemetry Store**: Self-hosted SigNoz (ClickHouse + OTel Collector) on port 8080.
2. **MCP Interface**: `signoz-mcp-server` running locally on port 8000, exposing structured JSON-RPC observability tools over HTTP.
   - **Schema Whitelist (6 Core RCA Tools)**: To prevent context window exhaustion and maintain fast local inference on Apple Silicon, our bridge whitelists exactly 6 essential tools covering the complete SRE diagnostic chain:
     1. `signoz_list_services` (List services)
     2. `signoz_list_alerts` (Check alerts)
     3. `signoz_query_metrics` (Query metrics)
     4. `signoz_search_traces` (Query traces)
     5. `signoz_get_trace_details` (Inspect trace spans)
     6. `signoz_search_logs` (Query logs)
   - **Precise Token Reduction**: Filtering from the full 41-tool schema (188,751 chars / ~47,187 tokens) down to these 6 core RCA tools (16,097 chars / ~4,024 tokens) achieves an exact **91.47% reduction** in LLM prompt payload size.
3. **Local LLM**: Ollama serving `qwen2.5:3b` locally on port 11434, utilizing Apple Silicon Metal acceleration and 4-bit quantization (~2.2 GB RAM) for fast token generation and accurate function calling.
