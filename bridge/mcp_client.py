import os
import json
import time
import httpx
from typing import List, Dict, Any, Optional, Union

AUDIT_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tool_calls.log")

class SigNozMCPClient:
    def __init__(self, url: str, api_key: str):
        self.url = url
        self.api_key = api_key
        self.headers = {
            "SIGNOZ-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        # Core SRE diagnostic query tools (6 tools) covering the complete RCA chain:
        # 1. signoz_list_services (List services)
        # 2. signoz_list_alerts (Check alerts)
        # 3. signoz_query_metrics (Query metrics)
        # 4. signoz_search_traces (Query traces)
        # 5. signoz_get_trace_details (Inspect trace spans)
        # 6. signoz_search_logs (Query logs)
        self.core_sre_tools = {
            "signoz_list_services",
            "signoz_list_alerts",
            "signoz_query_metrics",
            "signoz_search_traces",
            "signoz_get_trace_details",
            "signoz_search_logs"
        }

    def _log_audit(self, action: str, tool_name: str, payload: Any, status: str = "SUCCESS", duration_ms: float = 0.0):
        """Logs timestamped zero-egress audit entry to local file and console."""
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "action": action,
            "tool_name": tool_name,
            "endpoint": self.url,
            "status": status,
            "duration_ms": round(duration_ms, 2),
            "payload": payload
        }
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Console colored print for visibility
        color = "\033[92m" if status == "SUCCESS" else "\033[91m"
        print(f"{color}[AUDIT - ZERO EGRESS] {entry['timestamp']} | Tool: {tool_name} | {status} ({duration_ms:.1f}ms)\033[0m")

    def get_tools(self, filter_heavy_schemas: bool = True) -> List[Dict[str, Any]]:
        """Fetches tools from SigNoz MCP server and formats as OpenAI function schemas."""
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time()),
            "method": "tools/list",
            "params": {}
        }
        t0 = time.time()
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(self.url, headers=self.headers, json=payload)
                res.raise_for_status()
                data = res.json()
        except Exception as e:
            self._log_audit("tools/list", "ALL", str(e), status="ERROR", duration_ms=(time.time()-t0)*1000)
            raise RuntimeError(f"Failed to fetch tools from SigNoz MCP: {e}")

        mcp_tools = data.get("result", {}).get("tools", [])
        openai_tools = []
        for t in mcp_tools:
            name = t["name"]
            if filter_heavy_schemas and name not in self.core_sre_tools:
                continue
            
            schema = t.get("inputSchema", {"type": "object", "properties": {}})
            if "properties" in schema and isinstance(schema["properties"], dict):
                # Remove complex/error-prone filter parameters to ensure reliable 3B LLM tool calling
                for problematic_key in ["filter", "searchText", "searchContext"]:
                    schema["properties"].pop(problematic_key, None)

            desc = t.get("description", "")
            if "Examples:" in desc:
                desc = desc.split("Examples:")[0].strip()

            openai_tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": desc,
                    "parameters": schema
                }
            })
        
        self._log_audit("tools/list", "ALL", f"Loaded {len(openai_tools)} tools (filtered={filter_heavy_schemas})", duration_ms=(time.time()-t0)*1000)
        return openai_tools

    def call_tool(self, name: str, arguments: Union[str, Dict[str, Any]]) -> str:
        """Executes a tool call against the local SigNoz MCP endpoint."""
        if isinstance(arguments, str):
            try:
                args_dict = json.loads(arguments) if arguments.strip() else {}
            except Exception:
                args_dict = {}
        else:
            args_dict = arguments or {}

        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time()),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": args_dict
            }
        }

        t0 = time.time()
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(self.url, headers=self.headers, json=payload)
                res.raise_for_status()
                data = res.json()
        except Exception as e:
            err_msg = f"HTTP error calling {name}: {e}"
            self._log_audit("tools/call", name, {"arguments": args_dict, "error": err_msg}, status="ERROR", duration_ms=(time.time()-t0)*1000)
            return json.dumps({"error": err_msg})

        if "error" in data:
            err_msg = data["error"]
            self._log_audit("tools/call", name, {"arguments": args_dict, "error": err_msg}, status="ERROR", duration_ms=(time.time()-t0)*1000)
            return json.dumps({"error": err_msg})

        result = data.get("result", {})
        content_items = result.get("content", [])
        output_str = ""
        for item in content_items:
            if item.get("type") == "text":
                text_val = item.get("text", "")
                if text_val.startswith("note:") or "more results likely exist" in text_val:
                    continue
                output_str += text_val + "\n"
        
        if not output_str.strip():
            output_str = json.dumps(result.get("structuredContent", result))

        output_str = output_str.strip()

        if name in ["signoz_search_logs", "signoz_search_traces"] and output_str.startswith("{"):
            try:
                parsed = json.loads(output_str)
                if name == "signoz_search_logs":
                    rows = parsed.get("data", {}).get("data", {}).get("results", [{}])[0].get("rows", [])
                    clean_logs = []
                    for r in rows:
                        clean_logs.append({
                            "timestamp": r.get("timestamp"),
                            "service": r.get("data", {}).get("attributes_string", {}).get("service.name", args_dict.get("service", "unknown")),
                            "message": r.get("data", {}).get("body", r.get("body", ""))
                        })
                    if clean_logs:
                        output_str = json.dumps({"logs": clean_logs}, indent=2)
                elif name == "signoz_search_traces":
                    rows = parsed.get("data", {}).get("data", {}).get("results", [{}])[0].get("rows", [])
                    clean_traces = []
                    for r in rows:
                        d = r.get("data", {})
                        clean_traces.append({
                            "trace_id": r.get("traceID", d.get("trace_id", "")),
                            "timestamp": r.get("timestamp"),
                            "service": d.get("service.name", args_dict.get("service", "unknown")),
                            "operation": d.get("name", ""),
                            "duration_ms": round(d.get("durationNano", 0) / 1000000.0, 2),
                            "http_status_code": d.get("http.status_code"),
                            "error": d.get("has_error", True)
                        })
                    if clean_traces:
                        output_str = json.dumps({"traces": clean_traces}, indent=2)
            except Exception:
                pass
        self._log_audit("tools/call", name, {"arguments": args_dict, "response_preview": output_str[:200]}, duration_ms=(time.time()-t0)*1000)
        return output_str
