from typing import Optional, Any, TypeVar, Generic, Collection
from pydantic import BaseModel

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: Optional[str] = None
    data: Optional[T] = None
    errors: Optional[Collection] = None