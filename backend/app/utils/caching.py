from functools import wraps
from fastapi import Request
from app.core.config import settings
import aioredis
import json

redis = aioredis.from_url(settings.REDIS_URL)

def cache_response(expire_seconds: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            if request.method != "GET":
                return await func(*args, request=request, **kwargs)

            cache_key = f"cache:{request.url.path}"
            cached = await redis.get(cache_key)
            
            if cached:
                return json.loads(cached)
            
            response = await func(*args, request=request, **kwargs)
            await redis.setex(cache_key, expire_seconds, json.dumps(response))
            return response
        return wrapper
    return decorator