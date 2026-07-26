import os
import sys
import json
from typing import List, Dict, Any
from openai import OpenAI

# Ensure we can import local modules when run from anywhere
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bridge.mcp_client import SigNozMCPClient

def load_env():
    """Loads environment variables from .env in root directory."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key not in os.environ:
                        os.environ[key] = val

SYSTEM_PROMPT = """You are a Zero-Egress SRE Copilot for SigNoz performing Root Cause Analysis (RCA).

GUIDELINES:
1. NEVER use the 'filter', 'searchText', or 'operation' parameters in tool calls.
2. Step 1: Call `signoz_search_traces` with {"error": true, "limit": 5} to find failing microservices.
3. Step 2: Extract the failing service name from the trace (e.g. paymentservice, recommendationservice, checkoutservice) and call `signoz_search_logs` with {"service": "<failing_service>", "limit": 5} to get the stack trace.
4. STOPPING RULE: Once you receive the failing trace and log message (e.g. OutOfMemoryError, 15s GC pause, HikariPool timeout, Redis connection refused), DO NOT call any more tools. Immediately explain the Root Cause Analysis in plain text naming the failing service and root cause."""

def run_loop(query: str, client: OpenAI, mcp: SigNozMCPClient, tools: List[Dict[str, Any]], max_steps: int = 8) -> str:
    """Runs the RCA tool-calling loop between local Qwen and SigNoz MCP server."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]
    
    model_name = os.environ.get("MODEL_NAME", "qwen2.5:3b")
    
    for step in range(max_steps):
        print(f"\033[90m[Step {step+1}/{max_steps}] Querying Qwen 2.5 3B...\033[0m")
        try:
            res = client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=tools,
                temperature=0.1,
                max_tokens=1024
            )
        except Exception as e:
            return f"❌ Error communicating with local LLM server: {e}"
            
        msg = res.choices[0].message
        
        # Check if the model requested any tool calls
        if msg.tool_calls:
            # Format assistant message for history
            assistant_msg = {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in msg.tool_calls
                ]
            }
            messages.append(assistant_msg)
            
            for tc in msg.tool_calls:
                t_name = tc.function.name
                t_args = tc.function.arguments
                print(f"\033[96m🤖 Qwen requested tool: \033[1m{t_name}\033[0m \033[96m({t_args})\033[0m")
                
                # Execute against MCP
                result_str = mcp.call_tool(t_name, t_args)
                
                # Truncate if response is too large to prevent overflowing 3B local LLM context
                if len(result_str) > 3000:
                    display_res = result_str[:3000] + "\n... [Output truncated for context window]"
                else:
                    display_res = result_str
                
                print(f"\033[92m⚡ MCP response ({len(result_str)} chars):\033[0m {display_res[:150]}...")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": t_name,
                    "content": display_res
                })
        else:
            # Final natural language response reached
            return msg.content or "No response generated."
            
    return "⚠️ Tool loop reached max steps without final answer."

def main():
    load_env()
    
    api_key = os.environ.get("SIGNOZ_API_KEY", "")
    mcp_url = os.environ.get("SIGNOZ_MCP_URL", "http://localhost:8000/mcp")
    llm_url = os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1")
    
    if not api_key:
        print("⚠️ Warning: SIGNOZ_API_KEY is not set in environment or .env file.")
        
    print(f"🔗 Connecting to SigNoz MCP at: {mcp_url}")
    print(f"🧠 Connecting to Local Qwen at: {llm_url}")
    
    mcp = SigNozMCPClient(url=mcp_url, api_key=api_key)
    try:
        tools = mcp.get_tools(filter_heavy_schemas=True)
    except Exception as e:
        print(f"❌ Could not load tools from MCP: {e}")
        return

    client = OpenAI(base_url=llm_url, api_key="local-zero-egress")
    
    # CLI mode: single query passed via command line arguments
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"\n❓ User Query: \033[1m{query}\033[0m\n" + "-"*50)
        answer = run_loop(query, client, mcp, tools)
        print("\n" + "-"*50)
        print(f"\033[93m🏁 SRE Copilot Diagnosis:\033[0m\n{answer}\n")
        return

    # Interactive REPL mode
    print("\n" + "="*60)
    print("🛡️  Zero-Egress SRE Copilot (SigNoz MCP <-> Local Qwen 3B)")
    print("Type your query below (or 'exit' / 'quit' to close)")
    print("="*60 + "\n")
    
    while True:
        try:
            query = input("\033[94mSRE Copilot > \033[0m").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "q"]:
                print("👋 Exiting SRE Copilot.")
                break
            print("\n" + "-"*50)
            answer = run_loop(query, client, mcp, tools)
            print("-"*50)
            print(f"\033[93m🏁 SRE Copilot Diagnosis:\033[0m\n{answer}\n")
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Exiting SRE Copilot.")
            break

if __name__ == "__main__":
    main()
