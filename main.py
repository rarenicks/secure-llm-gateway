import os
import time
import httpx
from typing import List, Optional, Dict, Any, Union
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Local modules
from guardrails_config import GuardrailsEngine, GuardrailResult
from logger import init_db, log_request

# Load environment variables
load_dotenv()

TARGET_LLM_URL = os.getenv("TARGET_LLM_URL", "http://localhost:11434/v1/chat/completions")
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "False").lower() == "true"

# --- Pydantic Models (OpenAI Compatible) ---

class ChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None

# --- Lifespan Manager ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    pass

app = FastAPI(title="Enterprise GenAI Security Gateway", version="1.0.0", lifespan=lifespan)
guardrails = GuardrailsEngine()
http_client = httpx.AsyncClient()

# --- Dependencies ---

def get_guardrails():
    return guardrails

# --- Endpoints ---

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    background_tasks: BackgroundTasks,
    raw_request: Request,
    guards: GuardrailsEngine = Depends(get_guardrails)
):
    start_time = time.time()
    
    # 1. Extract the last user message for scanning
    last_user_message = next((m for m in reversed(request.messages) if m.role == "user"), None)
    
    if not last_user_message:
        # If no user message found, just pass through or error? 
        # For security, let's assume valid requests must have a user prompt.
        # But system messages might be present. Let's scan the last message regardless of role if 'user' specific logic matches.
        # For this MVP, we focus on the last message.
        input_text = request.messages[-1].content if request.messages else ""
    else:
        input_text = last_user_message.content

    client_ip = raw_request.client.host if raw_request.client else "unknown"

    # 2. Apply Guardrails
    result: GuardrailResult = guards.validate(input_text)
    
    # 3. Handle Blocked Requests
    if not result.valid:
        latency = time.time() - start_time
        # Log failure
        background_tasks.add_task(
            log_request,
            client_ip=client_ip,
            original_prompt=input_text,
            sanitized_prompt=result.sanitized_text,
            verdict="BLOCKED: " + (result.reason or "Unknown"),
            latency=latency,
            metadata={"action": result.action}
        )
        
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "message": f"Request blocked by security guardrails: {result.reason}",
                    "type": "invalid_request_error",
                    "code": "security_policy_violation"
                }
            }
        )

    # 4. Reconstruct Request with Sanitized Input
    # We update the *last* user message content with the sanitized version.
    # This ensures PII is stripped before sending to LLM.
    if last_user_message:
        last_user_message.content = result.sanitized_text
        # Note: request.messages is a list of objects, modifying the object *in place* might work if it's mutable,
        # but Pydantic v2 models are often immutable if frozen. 
        # Default BaseModel is not frozen.
        
        # Let's verify we are actually updating the list used for the downstream request.
        # We need to reconstruct the payload dict.
    
    payload = request.model_dump(exclude_unset=True)
    
    # 5. Proxy to LLM
    try:
        if USE_MOCK_LLM:
            # Simulate network delay
            # await asyncio.sleep(0.5) 
            response_data = {
                "id": "chatcmpl-mock",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"Mock Response. I received your sanitized message: '{result.sanitized_text}'"
                    },
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            }
            status_code = 200
        else:
            # Real Proxy
            upstream_response = await http_client.post(
                TARGET_LLM_URL,
                json=payload,
                timeout=60.0 # generous timeout for local LLMs
            )
            status_code = upstream_response.status_code
            if status_code != 200:
                # Setup error handling for upstream
                try:
                    response_data = upstream_response.json()
                except:
                    response_data = {"error": "Upstream error", "details": upstream_response.text}
            else:
                response_data = upstream_response.json()

    except Exception as e:
        status_code = 502 # Bad Gateway
        response_data = {"error": "Failed to connect to upstream LLM", "details": str(e)}

    # 6. Log Success (Background)
    latency = time.time() - start_time
    background_tasks.add_task(
        log_request,
        client_ip=client_ip,
        original_prompt=input_text, # We verify original
        sanitized_prompt=result.sanitized_text, # We verify sanitized
        verdict="PASSED" if status_code == 200 else f"FAILED_UPSTREAM_{status_code}",
        latency=latency,
        metadata={"model": request.model, "mock": USE_MOCK_LLM}
    )

    return JSONResponse(status_code=status_code, content=response_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
