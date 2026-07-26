#!/usr/bin/env python3
import sys
import json
import urllib.request
import urllib.error
import time

API_URL = "http://localhost:11434/v1/chat/completions"
MODEL_ID = "qwen2.5:3b"

# ANSI color codes
COLOR_RESET = "\033[0m"
COLOR_CYAN = "\033[1;36m"
COLOR_GREEN = "\033[1;32m"
COLOR_YELLOW = "\033[1;33m"
COLOR_GRAY = "\033[2;37m"
COLOR_RED = "\033[1;31m"
COLOR_BOLD = "\033[1m"

def print_banner():
    print(f"{COLOR_BOLD}{COLOR_GREEN}")
    print("=========================================================================")
    print("⚡ QWEN 2.5 3B REAL-TIME STREAMING TERMINAL AGENT")
    print("=========================================================================")
    print(f"{COLOR_RESET}Connected to local server: {COLOR_CYAN}{API_URL}{COLOR_RESET}")
    print(f"{COLOR_GRAY}Commands:{COLOR_RESET}")
    print(f"  {COLOR_YELLOW}/clear{COLOR_RESET}   - Reset conversation memory")
    print(f"  {COLOR_YELLOW}/system{COLOR_RESET}  - Change system prompt")
    print(f"  {COLOR_YELLOW}/history{COLOR_RESET} - View current message stack")
    print(f"  {COLOR_YELLOW}/exit{COLOR_RESET}    - Quit the terminal agent\n")

def stream_query(messages):
    payload = {
        "model": MODEL_ID,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 512,
        "stream": True
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, headers={"Content-Type": "application/json"})
    
    full_response = []
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            for line in response:
                line_str = line.decode("utf-8").strip()
                if not line_str or not line_str.startswith("data: "):
                    continue
                data_str = line_str[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        print(content, end="", flush=True)
                        full_response.append(content)
                except Exception:
                    pass
        print() # Newline after stream finishes
        return "".join(full_response), None
    except urllib.error.URLError as e:
        print(f"\n{COLOR_RED}Error connecting to server ({API_URL}): {e}{COLOR_RESET}")
        return None, None
    except Exception as e:
        print(f"\n{COLOR_RED}Error: {e}{COLOR_RESET}")
        return None, None

def main():
    print_banner()
    
    system_prompt = "You are an intelligent, helpful AI coding and observability assistant. Provide concise and direct answers."
    messages = [{"role": "system", "content": system_prompt}]
    
    while True:
        try:
            user_input = input(f"{COLOR_CYAN}You > {COLOR_RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{COLOR_GREEN}Goodbye! 👋{COLOR_RESET}")
            break
            
        if not user_input:
            continue
            
        if user_input.lower() in ["/exit", "/quit", "quit", "exit"]:
            print(f"\n{COLOR_GREEN}Goodbye! 👋{COLOR_RESET}")
            break
            
        if user_input.lower() == "/clear":
            messages = [{"role": "system", "content": system_prompt}]
            print(f"{COLOR_YELLOW}🧹 Conversation history cleared!{COLOR_RESET}\n")
            continue
            
        if user_input.lower() == "/history":
            print(f"\n{COLOR_YELLOW}--- Current Message Stack ({len(messages)} msgs) ---{COLOR_RESET}")
            for m in messages:
                role_col = COLOR_GREEN if m["role"] == "assistant" else (COLOR_CYAN if m["role"] == "user" else COLOR_GRAY)
                print(f"{role_col}[{m['role'].upper()}]:{COLOR_RESET} {m['content']}")
            print(f"{COLOR_YELLOW}-----------------------------------------{COLOR_RESET}\n")
            continue
            
        if user_input.lower().startswith("/system"):
            new_sys = user_input[7:].strip()
            if new_sys:
                system_prompt = new_sys
                messages[0]["content"] = system_prompt
                print(f"{COLOR_YELLOW}⚙️ System prompt updated to:{COLOR_RESET} \"{system_prompt}\"\n")
            else:
                print(f"{COLOR_YELLOW}Current system prompt:{COLOR_RESET} \"{system_prompt}\"\n")
            continue
            
        messages.append({"role": "user", "content": user_input})
        
        print(f"{COLOR_GREEN}🤖 Qwen > {COLOR_RESET}", end="", flush=True)
        start_t = time.time()
        
        reply, _ = stream_query(messages)
        elapsed = time.time() - start_t
        
        if reply:
            messages.append({"role": "assistant", "content": reply})
            print(f"{COLOR_GRAY}(Completed in {elapsed:.2f}s){COLOR_RESET}\n")
        else:
            messages.pop()
            print()

if __name__ == "__main__":
    main()
