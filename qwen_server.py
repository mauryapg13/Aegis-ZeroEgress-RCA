import time
import uuid
import json
import re
from threading import Thread
from typing import List, Optional, Dict, Any, Union
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
import uvicorn

MODEL_ID = "Qwen/Qwen2.5-3B-Instruct"

print("=========================================================================")
print(f"🚀 Loading {MODEL_ID} optimized for Apple Silicon (FP16/MPS)...")
print("=========================================================================")

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16 if torch.backends.mps.is_available() else "auto",
    device_map="mps" if torch.backends.mps.is_available() else "auto"
)
print(f"\n✅ {MODEL_ID} loaded successfully into {model.device} memory!\n")

app = FastAPI(title="Qwen 2.5 3B High-Speed Tool-Calling Server")

class ChatMessage(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = MODEL_ID
    messages: List[Dict[str, Any]]
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Any] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    max_tokens: Optional[int] = 1024
    stream: Optional[bool] = False
    
    class Config:
        extra = "ignore"

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_ID,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "user"
            }
        ]
    }

def parse_tool_calls(text: str) -> List[Dict[str, Any]]:
    # Extract <tool_call>...</tool_call> blocks
    matches = re.findall(r"<tool_call>\s*(.*?)\s*</tool_call>", text, re.DOTALL)
    parsed = []
    for m in matches:
        try:
            data = json.loads(m.strip())
            name = data.get("name")
            args = data.get("arguments", {})
            if isinstance(args, dict):
                args_str = json.dumps(args)
            else:
                args_str = str(args)
            parsed.append({
                "id": f"call_{uuid.uuid4().hex[:8]}",
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": args_str
                }
            })
        except Exception as e:
            print(f"Failed to parse tool call JSON: {m} -> {e}")
    return parsed

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    try:
        # Pass tools if provided
        prompt_text = tokenizer.apply_chat_template(
            req.messages,
            tools=req.tools,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = tokenizer([prompt_text], return_tensors="pt").to(model.device)
        
        max_new_toks = req.max_tokens or 1024
        req_id = f"chatcmpl-{uuid.uuid4().hex}"
        created_time = int(time.time())
        
        if req.stream:
            streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
            generation_kwargs = dict(
                **model_inputs,
                streamer=streamer,
                max_new_tokens=max_new_toks,
                temperature=max(0.01, req.temperature or 0.7),
                top_p=req.top_p or 0.9,
                do_sample=(req.temperature or 0.7) > 0.01
            )
            
            thread = Thread(target=model.generate, kwargs=generation_kwargs)
            thread.start()
            
            def event_generator():
                full_text = []
                for new_text in streamer:
                    if new_text:
                        full_text.append(new_text)
                        # We stream delta content
                        chunk = {
                            "id": req_id,
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": req.model or MODEL_ID,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": new_text},
                                    "finish_reason": None
                                }
                            ]
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                
                # Check if full_text contained tool_calls
                complete_str = "".join(full_text)
                t_calls = parse_tool_calls(complete_str)
                if t_calls:
                    # Send tool calls chunk
                    tc_chunk = {
                        "id": req_id,
                        "object": "chat.completion.chunk",
                        "created": created_time,
                        "model": req.model or MODEL_ID,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"tool_calls": t_calls, "content": None},
                                "finish_reason": "tool_calls"
                            }
                        ]
                    }
                    yield f"data: {json.dumps(tc_chunk)}\n\n"
                else:
                    final_chunk = {
                        "id": req_id,
                        "object": "chat.completion.chunk",
                        "created": created_time,
                        "model": req.model or MODEL_ID,
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                    }
                    yield f"data: {json.dumps(final_chunk)}\n\n"
                yield "data: [DONE]\n\n"
                
            return StreamingResponse(event_generator(), media_type="text/event-stream")
        else:
            with torch.no_grad():
                outputs = model.generate(
                    **model_inputs,
                    max_new_tokens=max_new_toks,
                    temperature=max(0.01, req.temperature or 0.7),
                    top_p=req.top_p or 0.9,
                    do_sample=(req.temperature or 0.7) > 0.01
                )
            out_ids = [out[len(inp):] for inp, out in zip(model_inputs.input_ids, outputs)]
            resp_text = tokenizer.batch_decode(out_ids, skip_special_tokens=True)[0].strip()
            
            t_calls = parse_tool_calls(resp_text)
            if t_calls:
                # Clean out `<tool_call>...</tool_call>` from content
                clean_content = re.sub(r"<tool_call>\s*.*?\s*</tool_call>", "", resp_text, flags=re.DOTALL).strip()
                return {
                    "id": req_id,
                    "object": "chat.completion",
                    "created": created_time,
                    "model": req.model or MODEL_ID,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": clean_content if clean_content else None,
                                "tool_calls": t_calls
                            },
                            "finish_reason": "tool_calls"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": model_inputs.input_ids.shape[1],
                        "completion_tokens": len(out_ids[0]),
                        "total_tokens": model_inputs.input_ids.shape[1] + len(out_ids[0])
                    }
                }
            else:
                return {
                    "id": req_id,
                    "object": "chat.completion",
                    "created": created_time,
                    "model": req.model or MODEL_ID,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": resp_text},
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": model_inputs.input_ids.shape[1],
                        "completion_tokens": len(out_ids[0]),
                        "total_tokens": model_inputs.input_ids.shape[1] + len(out_ids[0])
                    }
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("=========================================================================")
    print("⚡ High-Speed Tool-Calling Server running on port 8085")
    print("👉 Endpoint: http://localhost:8085/v1/chat/completions")
    print("=========================================================================")
    uvicorn.run(app, host="0.0.0.0", port=8085)
