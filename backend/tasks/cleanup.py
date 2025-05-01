import os
import re
import time
from datetime import timedelta
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.storage import user_storage

USERS_DIR = user_storage
TTL = timedelta(
    seconds=settings.CELERY_RESULT_EXPIRE_SECONDS
).seconds


def remove_unused_files(dir: Path, before: float, exclude: Optional[re.Pattern] = None):
    if exclude is None:
        for item in os.scandir(dir):
            if item.is_file() and os.path.getctime(item.path) < before:
                try:
                    os.remove(item.path)
                except:
                    pass
    else:
        for item in os.scandir(dir):
            if item.is_file() and os.path.getctime(item.path) < before and not exclude.match(item.name):
                try:
                    os.remove(item.path)
                except:
                    pass
        


def cleanup_results():
    t_minimum = time.time() - TTL

    for user_folder in USERS_DIR.list_dir():
        remove_unused_files(user_folder / user_storage.UPLOADED_IMG_DIR, t_minimum)


if __name__ == "__main__":
    cleanup_results()
