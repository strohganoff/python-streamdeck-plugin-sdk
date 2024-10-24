"""Custom exceptions used during validations of cli & config parsing."""
from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any


class DirectoryNotFoundError(FileNotFoundError):
    """Custom exception to indicate that a specified directory was not found."""
    def __init__(self, *args: Any, directory: Path):
        super().__init__(*args)
        self.directory = directory


class NotAFileError(NotADirectoryError):
    """Custom exception to indicate that a provided path is not a file."""
