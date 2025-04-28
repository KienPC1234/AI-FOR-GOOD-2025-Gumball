from fastapi import FastAPI, Request
from starlette.middleware import cors, base

from app.core.config import settings
from app.db.session import SessionLocal
from app.utils.db_wrapper import AsyncDBWrapper


class DBSessionMiddleware(base.BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.db = AsyncDBWrapper(SessionLocal())
        try:
            response = await call_next(request)
        finally:
            await request.state.db.close()
        return response
    

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