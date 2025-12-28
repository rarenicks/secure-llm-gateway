import glob
import os
import time
import httpx
import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Depends, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Local modules
from app.core.logger import init_db, log_request, DB_FILE
from app.core.router import LLMRouter
from app.core.adapters import APIAdapter
from app.core.rate_limit import RateLimitMiddleware

# New Enterprise Library Imports
from guardrails_lib.engine import GuardrailsEngine
from guardrails_lib.core import GuardrailResult
from guardrails_lib.factory import GuardrailsFactory

# Load environment variables
load_dotenv()

TARGET_LLM_URL = os.getenv("TARGET_LLM_URL", "http://localhost:11434/v1/chat/completions")
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "False").lower() == "true"
GUARDRAILS_PROFILE = os.getenv("GUARDRAILS_PROFILE", "configs/default.yaml")

router = LLMRouter()

# --- Helpers ---

def load_available_profiles():
    """Scans configs/ directory for yaml files."""
    profiles = []
    try:
        files = glob.glob("configs/*.yaml")
        for f in files:
            name = Path(f).name
            profiles.append({"name": name, "path": f})
    except Exception as e:
        print(f"Error loading profiles: {e}")
    return profiles

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

import sys

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        init_db()
        print(f"Server Startup: Loading Guardrails Profile from {GUARDRAILS_PROFILE}")
        # Validate Config Load
        GuardrailsFactory.load_from_file(GUARDRAILS_PROFILE)
    except Exception as e:
        print(f"CRITICAL: Security Engine Connection Failed: {e}")
        sys.exit(1)
        
    yield
    # Shutdown
    pass

app = FastAPI(title="Semantic Sentinel Gateway", version="3.1.0", lifespan=lifespan)
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)

# Initialize Enterprise Guardrails from Config Profile
# This is the "Sentinel Framework" in action
guardrails = GuardrailsFactory.load_from_file(GUARDRAILS_PROFILE)


http_client = httpx.AsyncClient()

# --- Dependencies ---

def get_guardrails():
    return guardrails

# --- API Endpoints ---

@app.get("/api/profiles")
async def get_profiles():
    """Returns list of available profiles and the active one."""
    global GUARDRAILS_PROFILE
    available = load_available_profiles()
    active_name = Path(GUARDRAILS_PROFILE).name
    return {
        "active_profile": active_name,
        "profiles": available
    }

@app.post("/api/profiles/switch")
async def switch_profile(data: Dict[str, str] = Body(...)):
    """Switches the active guardrails profile."""
    global guardrails, GUARDRAILS_PROFILE
    
    profile_name = data.get("profile_name")
    if not profile_name:
        raise HTTPException(status_code=400, detail="profile_name required")
        
    # Security: Ensure we only load from configs/ directory
    safe_name = Path(profile_name).name
    path = f"configs/{safe_name}"
    
    if not os.path.exists(path):
         raise HTTPException(status_code=404, detail="Profile not found")
         
    try:
        print(f"Switching Profile to: {path}")
        new_engine = GuardrailsFactory.load_from_file(path)
        guardrails = new_engine # Hot swap!
        GUARDRAILS_PROFILE = path
        return {"status": "success", "active_profile": safe_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load profile: {str(e)}")

@app.get("/api/logs")
async def get_logs():
    """Returns the latest 20 audit logs."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 20")
        rows = cursor.fetchall()
        logs = [dict(row) for row in rows]
        conn.close()
        return logs
    except Exception as e:
        return {"error": str(e)}

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
        input_text = request.messages[-1].content if request.messages else ""
    else:
        input_text = last_user_message.content

    client_ip = raw_request.client.host if raw_request.client else "unknown"

    # 2. Apply Guardrails (Input)
    result: GuardrailResult = guards.validate(input_text)
    
    # 3. Handle Blocked Requests
    if not result.valid and result.action == "blocked":
        latency = time.time() - start_time
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
    if last_user_message:
        last_user_message.content = result.sanitized_text
    
    payload = request.model_dump(exclude_unset=True)
    
    # 5. Route and Proxy to LLM
    try:
        if USE_MOCK_LLM:
            # Mock Response Logic
            response_data = {
                "id": "chatcmpl-mock",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"Mock Response ({request.model}). Sanitized Input: '{result.sanitized_text}'"
                    },
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            }
            status_code = 200
        else:
            # 5a. Determine Route
            target_url, headers, adapter_type = router.get_route(request.model)
            
            # 5b. Adapt Request
            if adapter_type == "anthropic":
                upstream_payload = APIAdapter.openai_to_anthropic(payload)
            elif adapter_type == "gemini":
                upstream_payload = APIAdapter.openai_to_gemini(payload)
            else:
                # OpenAI / Grok / Local (OpenAI-compatible)
                upstream_payload = payload
            
            # 5c. Send Request
            upstream_response = await http_client.post(
                target_url,
                json=upstream_payload,
                headers=headers,
                timeout=60.0
            )
            
            status_code = upstream_response.status_code
            if status_code != 200:
                try:
                    raw_error = upstream_response.json()
                    if "error" in raw_error:
                        if isinstance(raw_error["error"], dict) and "message" in raw_error["error"]:
                            response_data = raw_error
                        elif isinstance(raw_error["error"], dict) and "message" in raw_error["error"]: 
                             response_data = {"error": {"message": raw_error["error"]["message"]}}
                        else:
                             msg = str(raw_error["error"])
                             response_data = {"error": {"message": f"Upstream Error: {msg}"}}
                    else:
                        response_data = {"error": {"message": f"Upstream Error: {upstream_response.text}"}}
                except:
                    response_data = {"error": {"message": f"Upstream Error ({status_code}): {upstream_response.text}"}}
            else:
                raw_response = upstream_response.json()
                
                # 5d. Adapt Response
                if adapter_type == "anthropic":
                    response_data = APIAdapter.anthropic_to_openai(raw_response)
                elif adapter_type == "gemini":
                    response_data = APIAdapter.gemini_to_openai(raw_response, model=request.model)
                else:
                    response_data = raw_response

        # --- Output Guardrails (New) ---
        if status_code == 200 and "choices" in response_data and response_data["choices"]:
            # Check the first choice content
            output_msg = response_data["choices"][0]["message"]
            output_text = output_msg.get("content", "")
            
            if output_text:
                out_result = guards.validate_output(output_text)
                
                if not out_result.valid and out_result.action == "blocked":
                    # Block the response
                    status_code = 400
                    response_data = {
                        "error": {
                            "message": f"Response blocked by security guardrails: {out_result.reason}",
                            "type": "invalid_request_error",
                            "code": "security_policy_violation_output"
                        }
                    }
                elif out_result.sanitized_text != output_text:
                    # Redact content
                    response_data["choices"][0]["message"]["content"] = out_result.sanitized_text

    except Exception as e:
        status_code = 502 # Bad Gateway
        response_data = {"error": {"message": f"Gateway Connection Failed: {str(e)}"}}

    # 6. Log Success (Background)
    latency = time.time() - start_time
    background_tasks.add_task(
        log_request,
        client_ip=client_ip,
        original_prompt=input_text, 
        sanitized_prompt=result.sanitized_text,
        verdict="PASSED" if status_code == 200 else f"FAILED_{status_code}",
        latency=latency,
        metadata={"model": request.model, "mock": USE_MOCK_LLM}
    )

    return JSONResponse(status_code=status_code, content=response_data)

# --- UI Serving ---
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)