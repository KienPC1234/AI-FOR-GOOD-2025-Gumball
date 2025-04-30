import functools
import hashlib
import inspect
import os
import shutil
from abc import ABC, abstractmethod
from contextlib import contextmanager
from io import BufferedIOBase
from pathlib import Path
from typing import Optional, Callable, Generator

from app.core.config import settings
from app.states import DiskOperationError


EMPTY_PATH = Path("")


def _path_supplied(function):
    """
    Automatically apply the relative path under parameter `path` to the base directory and perform security check.
    """

    signature = inspect.signature(function)
    if "path" not in signature.parameters:
        return function

    @functools.wraps(function)
    def wrapper(self: 'Storage', *args, **kwargs):
        bound_args = signature.bind(self, *args, **kwargs)
        bound_args.apply_defaults()
        
        path_value = bound_args.arguments.get("path")
        if path_value is not None:
            bound_args.arguments["path"] = self._map_path(path_value, root_path=self.base_dir)
        else:
            bound_args.arguments["path"] = None
        
        return function(self, *bound_args.args, **bound_args.kwargs)
    
    return wrapper


class StorageBase(ABC):
    @abstractmethod
    def new_dir(self, path: Path) -> Path:
        raise NotImplementedError
    
    @abstractmethod
    def save_file(self, file: BufferedIOBase, path: Path) -> Path:
        raise NotImplementedError
    
    @abstractmethod
    def read_file(self, path: Path) -> BufferedIOBase:
        raise NotImplementedError

    @abstractmethod
    def delete_file(self, path: Path) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def delete_folder(self, path: Path) -> None:
        raise NotImplementedError

    @abstractmethod
    def exists(self, path: Path) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_dir(self, directory: Optional[Path] = None) -> Generator[Path, None, None]:
        raise NotImplementedError


class Storage(StorageBase):
    """
    `_base_dir`: top most directory
    `base_dir`: current directory
    """


    def __init__(self, base_subdir: Optional[Path] = None):
        self._root_dir = Path(settings.BASE_STORAGE_PATH).absolute()
        if base_subdir:
            self._root_dir = self._map_path(base_subdir)
        
        try:
            self._root_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise DiskOperationError(f"Failed to create base directory") from e
        
        self._cd = Path("")

    @property
    def base_dir(self):
        return self._root_dir / self._cd

    def _map_path(self, path: os.PathLike, root_path: Optional[Path] = None) -> Path:
        mapped = ((root_path or self._root_dir) / path).absolute()
        if not mapped.is_relative_to(self._root_dir):
            raise DiskOperationError(f"Path {path} is outside of the base directory.")
        return mapped
    
    @_path_supplied
    def new_dir(self, path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path

    @_path_supplied
    def save_file(self, file: BufferedIOBase, path: Path = Path("")) -> Path:
        """
        Store the content under the given path, then return the absolute path (relative to `self.base_dir`)
        """
        with path.open("wb") as f:
            f.write(file.read())
        return path
    
    @_path_supplied
    def read_file(self, path: Path = Path("")) -> BufferedIOBase:
        if path.exists():
            return path.open("rb")
        raise DiskOperationError(f"File {path} not found in storage.")

    @_path_supplied
    def delete_file(self, path: Path = Path("")) -> None:
        if not path.exists():
            raise DiskOperationError(f"File {path} not found in storage.")
        path.unlink()

    @_path_supplied
    def delete_folder(self, path: Path = Path("")) -> None:
        if not path.exists():
            raise DiskOperationError(f"Directory {path} not found in storage.")
        shutil.rmtree(path)

    def exists(self, path: os.PathLike = Path("")) -> bool:
        return self._map_path(path).exists()

    @_path_supplied
    def list_dir(self, path: Optional[Path] = None, files_only: bool = False, folders_only: bool = False) -> Generator[Path, None, None]:
        path = path or self.base_dir
        if files_only:
            return (f for f in path.iterdir() if f.is_file())
        elif folders_only:
            return (f for f in path.iterdir() if not f.is_file())
        return path.iterdir()
    
    def mountable(self, path: os.PathLike):
        return Mounted(self._map_path(path))
    
    @_path_supplied
    @contextmanager
    def cd(self, path: Path):
        if not path.exists():
            raise DiskOperationError("Invalid path")
        
        old_cd = self._cd
        try:
            self._cd = path.relative_to(self._root_dir)
            yield
        finally:
            self._cd = old_cd
        
    
    def absolute_of(self, path: os.PathLike):
        """
        Convert a path to absolute and also verify it
        """
        return self._map_path(path)
    
    def absolute(self) -> Path:
        """
        Get the absolute path of the base directory
        """
        return self.base_dir.absolute()
    
    def __fspath__(self) -> str:
        return self.base_dir.__fspath__()

    def avail_file_name(self,
            *,
            random_bytes_generator: Callable[[int], bytes] = os.urandom,
            bytes_length: int = 15,
            ext: Optional[str] = None
        ) -> Path:
        """
        Generate a random available file name in the directory.
        """
        
        random_provider = lambda: "".join(hex(x)[2:].rjust(2, '0') for x in random_bytes_generator(bytes_length))
        while self.exists(fname := random_provider()):
            pass
        return self._map_path(fname) + ext if ext else self._map_path(fname)
    

class Mounted(Storage):
    def __init__(self, path: os.PathLike):
        super().__init__(path)

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class UserStorage(Storage):
    RAW_IMG_DIR = Path("raw_imgs")
    JPEG_IMG_DIR = Path("jpeg_imgs")
    ANALYSIS_DIR = Path("analysis")


    def __init__(self):
        super().__init__(settings.BASE_USER_STORAGE_PATH)

    def user_dir(self, user_id: int) -> Mounted:
        return Mounted(self.base_dir / f"user_{user_id}")
    
    def user_raw_img_dir(self, user_id: int):
        return Mounted(self.base_dir / f"user_{user_id}" / self.RAW_IMG_DIR)
    
    def user_jpeg_img_dir(self, user_id: int):
        return Mounted(self.base_dir / f"user_{user_id}" / self.JPEG_IMG_DIR)
    
    def user_analysis_dir(self, user_id: int):
        return Mounted(self.base_dir / f"user_{user_id}" / self.ANALYSIS_DIR)
    
    def list_user_dir(self, user_id: int, *, as_tuple: bool = False):
        iterable = self.list_dir(self.user_dir(user_id))
        return (*iterable,) if as_tuple else iterable


# Instantiate the storage object
base_storage = Storage()
user_storage = UserStorage()