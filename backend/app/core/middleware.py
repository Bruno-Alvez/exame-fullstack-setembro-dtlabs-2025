from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import structlog
import time
from typing import Callable

logger = structlog.get_logger()


class RateLimitMiddleware:
    def __init__(self, app, calls: int = 100, period: int = 60):
        self.app = app
        self.calls = calls
        self.period = period
        self.clients = {}

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        request = Request(scope, receive)
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        if client_ip not in self.clients:
            self.clients[client_ip] = []
        
        self.clients[client_ip] = [
            call_time for call_time in self.clients[client_ip]
            if current_time - call_time < self.period
        ]
        
        if len(self.clients[client_ip]) >= self.calls:
            logger.warning("Rate limit exceeded", client_ip=client_ip)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"}
            )
        
        self.clients[client_ip].append(current_time)
        
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware:
    async def __call__(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class AuthErrorHandler:
    @staticmethod
    async def handle_auth_error(request: Request, exc: HTTPException):
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "detail": "Authentication required",
                    "error_code": "AUTH_REQUIRED"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "detail": "Insufficient permissions",
                    "error_code": "INSUFFICIENT_PERMISSIONS"
                }
            )
        else:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail}
            )
