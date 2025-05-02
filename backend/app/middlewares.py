import time
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware import cors, base

from app.core.config import settings
from app.utils import connect_async_db


class DBSessionMiddleware(base.BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.db = connect_async_db()
        try:
            response = await call_next(request)
        finally:
            await request.state.db.close()
        return response


class RateLimitMiddleware(base.BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        # Clean old requests
        self.requests[client_ip] = [req_time for req_time in self.requests[client_ip] 
                                  if now - req_time < 60]
        
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"}
            )
        
        self.requests[client_ip].append(now)
        return await call_next(request)
    

def apply_middlewares(app: FastAPI) -> None:
    """
    Apply middlewares to the FastAPI application.
    
    Args:
        app (FastAPI): The FastAPI application instance.
    """

    # Set all CORS enabled origins
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            cors.CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Add DB session middleware sharing the same session across the each route
    app.add_middleware(DBSessionMiddleware)