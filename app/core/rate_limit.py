import time
from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import threading

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self.lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        # Identify client (IP address)
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for static assets or non-API routes if needed
        if not request.url.path.startswith("/v1/"):
             return await call_next(request)

        with self.lock:
            current_time = time.time()
            # Clean up old requests
            self.requests[client_ip] = [
                t for t in self.requests[client_ip] 
                if current_time - t < self.window_seconds
            ]
            
            # Check limit
            if len(self.requests[client_ip]) >= self.max_requests:
                return Response(
                    content="Rate limit exceeded. Please try again later.", 
                    status_code=429
                )
            
            # Record new request
            self.requests[client_ip].append(current_time)

        response = await call_next(request)
        return response
