import aiofiles
from pathlib import Path
from typing import Union


async def async_save_file(directory: Union[str, Path], file, filename: str = None) -> Path:
    """
    Save a file asynchronously to the specified directory.

    Args:
        directory (Union[str, Path]): The directory where the file will be saved.
        file: The file-like object to save.
        filename (str, optional): The name of the file. If not provided, the original file name is used.

    Returns:
        Path: The path to the saved file.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    filename = filename or file.filename
    file_path = directory / filename

    async with aiofiles.open(file_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # Read in chunks of 1 MB
            await f.write(chunk)

    return file_path


async def async_read_file(file_path: Union[str, Path]) -> bytes:
    """
    Read a file asynchronously.

    Args:
        file_path (Union[str, Path]): The path to the file.

    Returns:
        bytes: The content of the file.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    async with aiofiles.open(file_path, "rb") as f:
        return await f.read()


async def async_delete_file(file_path: Union[str, Path]) -> None:
    """
    Delete a file asynchronously.

    Args:
        file_path (Union[str, Path]): The path to the file.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    await aiofiles.os.remove(file_path)


async def async_file_exists(file_path: Union[str, Path]) -> bool:
    """
    Check if a file exists asynchronously.

    Args:
        file_path (Union[str, Path]): The path to the file.

    Returns:
        bool: True if the file exists, False otherwise.
    """
    file_path = Path(file_path)
    return file_path.exists()