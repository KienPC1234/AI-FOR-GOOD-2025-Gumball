from datetime import datetime, timezone
from os import path as path_tool, PathLike
from uuid import uuid4

from app.db.session import SessionLocal
from .db_wrapper import AsyncDBWrapper, DBWrapper
from .lazy import lazy_bound_function, lazy_load_function
from .ranges import TimeRange, AnyTime
from .saver import save_analyzation_output, load_analyzation_output  # , load_heatmap, save_heatmap


def change_fext(path: PathLike, ext: str):
    return path_tool.splitext(path)[0] + ext

def get_fext(path: PathLike):
    return path_tool.splitext(path)[1]

def utcnow():
    return datetime.now(timezone.utc)

def uuid():
    """
    Generate a random uuid hex
    """
    return uuid4().hex

def connect_async_db() -> AsyncDBWrapper:
    """
    Return a new database session wrapped with `AsyncDBWrapper`
    """
    return AsyncDBWrapper(SessionLocal())

def connect_db() -> DBWrapper:
    """
    Return a new database session wrapped with `AsyncDBWrapper`
    """
    return DBWrapper(SessionLocal())