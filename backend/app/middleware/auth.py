from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request


class JWTMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Forward request to downstream handlers where auth dependencies validate JWT
        response = await call_next(request)
        return response
