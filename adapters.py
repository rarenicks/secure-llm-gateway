from typing import Dict, Any, List

class APIAdapter:
    @staticmethod
    def openai_to_anthropic(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts OpenAI ChatCompletion format to Anthropic Messages API format.
        """
        messages = request_data.get("messages", [])
        system_prompt = None
        
        # Extract system prompt if present (Anthropic treats it separately)
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                filtered_messages.append(msg)
        
        payload = {
            "model": request_data.get("model"),
            "messages": filtered_messages,
            "max_tokens": request_data.get("max_tokens", 1024), # Anthropic requires max_tokens
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        return payload

    @staticmethod
    def anthropic_to_openai(response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts Anthropic response to OpenAI format.
        """
        content = ""
        if "content" in response_data and isinstance(response_data["content"], list):
             # Anthropic returns a list of content blocks
             for block in response_data["content"]:
                 if block["type"] == "text":
                     content += block["text"]
        
        return {
            "id": response_data.get("id"),
            "object": "chat.completion",
            "created": 0, # Timestamp not always compatible
            "model": response_data.get("model"),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop" # Simplified
            }],
            "usage": {
                "prompt_tokens": response_data.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": response_data.get("usage", {}).get("output_tokens", 0),
                "total_tokens": 0
            }
        }

    @staticmethod
    def openai_to_gemini(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts OpenAI format to Google Gemini generateContent format.
        """
        messages = request_data.get("messages", [])
        contents = []
        system_instruction = None

        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
                continue
            
            # Map roles: user->user, assistant->model
            gemini_role = "user" if role == "user" else "model"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })
            
        payload = {
            "contents": contents,
             "generationConfig": {
                "maxOutputTokens": request_data.get("max_tokens"),
                "temperature": request_data.get("temperature"),
                "topP": request_data.get("top_p")
            }
        }
        
        if system_instruction:
             payload["systemInstruction"] = system_instruction
             
        # Safety settings could be added here
        return payload

    @staticmethod
    def gemini_to_openai(response_data: Dict[str, Any], model: str) -> Dict[str, Any]:
        """
        Converts Gemini response to OpenAI format.
        """
        content = ""
        try:
            # Gemini response structure can be nested
            candidates = response_data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    content = parts[0].get("text", "")
        except Exception:
            content = "Error parsing Gemini response"

        return {
            "id": "gemini-response",
            "object": "chat.completion",
            "created": 0,
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }],
             "usage": {
                "prompt_tokens": 0, # Gemini metadata parsing is complex
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
