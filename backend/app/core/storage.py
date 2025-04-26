import functools
import hashlib
import inspect
import os
import shutil
from _typeshed import ReadableBuffer
from abc import ABC, abstractmethod
from config import settings
from io import BufferedIOBase
from pathlib import Path
from typing import Optional, Callable, Generator


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
    def __init__(self, base_subdir: Optional[Path] = None):
        self._base_dir = Path(settings.BASE_STORAGE_PATH)
        if base_subdir:
            self._base_dir = self._map_path(base_subdir)
        
        try:
            self._base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create base directory") from e

    @property
    def base_dir(self):
        return self._base_dir

    def _map_path(self, path: os.PathLike, base_path: Optional[Path] = None) -> Path:
        mapped = ((base_path or self.base_dir) / path).absolute()
        if not mapped.relative_to(self.base_dir):
            raise ValueError(f"Path {path} is outside of the base directory.")
        return mapped
    
    @staticmethod
    def _path_supplied(function: Callable):
        """
        Automatically apply the relative path under parameter `path` to the base directory and perform security check.
        """

        signature = inspect.signature(function)

        if "path" not in signature.parameters:
            return function

        @functools.wraps(function)
        def wrapper(self: Storage, *args, **kwargs):
            bound_args = signature.bind(self, *args, **kwargs)
            bound_args.apply_defaults()
            
            path_value = bound_args.arguments.get("path")
            bound_args.arguments["path"] = self._map_path(path_value) if path_value is not None else path_value
            
            return function(self, *bound_args.args, **bound_args.kwargs)
        
        return wrapper
    
    @_path_supplied
    def new_dir(self, path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path

    @_path_supplied
    def save_file(self, file: BufferedIOBase, path: Path) -> Path:
        """
        Store the content under the given path, then return the absolute path (relative to `self.base_dir`)
        """
        with path.open("wb") as f:
            f.write(file.read())
        return path
    
    @_path_supplied
    def read_file(self, path: Path) -> BufferedIOBase:
        if path.exists():
            return path.open("rb")
        raise FileNotFoundError(f"File {path} not found in storage.")

    @_path_supplied
    def delete_file(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"File {path} not found in storage.")
        path.unlink()

    @_path_supplied
    def delete_folder(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Directory {path} not found in storage.")
        shutil.rmtree(path)

    def exists(self, path: os.PathLike) -> bool:
        return self._map_path(path).exists()

    @_path_supplied()
    def list_dir(self, path: Optional[Path] = None, files_only: bool = False, folders_only: bool = False) -> Generator[Path, None, None]:
        path = path or self.base_dir
        if files_only:
            return (f for f in path.iterdir() if f.is_file())
        elif folders_only:
            return (f for f in path.iterdir() if not f.is_file())
        return path.iterdir()
    
    def mountable(self, path: os.PathLike):
        return Mounted(self, path)
    
    def absolute_of(self, path: os.PathLike):
        return self._map_path(path)
    
    def absolute(self) -> Path:
        return self.base_dir.absolute()
    
    def __fspath__(self) -> str:
        return self.base_dir.__fspath__()

    def available_file_name(self,
            *,
            random_bytes_generator: Callable[[int], bytes] = os.urandom,
            bytes_length: int = 15
        ) -> Path:
        """
        Generate a random available file name in the directory.
        """
        
        random_provider = lambda: "".join(hex(x)[2:].rjust(2, '0') for x in random_bytes_generator(bytes_length))
        while self.exists(fname := random_provider()):
            pass
        return self._map_path(fname)
    

class Mounted(Storage):
    def __init__(self, storage: Storage, path: os.PathLike):
        super().__init__(path)

        self.storage = storage

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    @Storage._path_supplied
    def mount(self, path: Path) -> None:
        self.path = path
        return self


class UserStorage(Storage):
    def __init__(self):
        super().__init__(settings.BASE_USER_STORAGE_PATH)

    def get_user_folder(self, user_id: int) -> Mounted:
        return Mounted(self, f"user_{user_id}")

# Instantiate the storage object
base_storage = Storage()
user_storage = UserStorage()