"""Helpers shared by converters."""

from pathlib import Path

from konwerter.errors import InvalidInputError


def read_utf8(path: Path) -> str:
    """Read a UTF-8 text file (with or without BOM), keeping line endings untouched."""
    try:
        with path.open(encoding="utf-8-sig", newline="") as file:
            return file.read()
    except UnicodeDecodeError as error:
        raise InvalidInputError(
            f"{path.name} is not valid UTF-8 text. Save the file with UTF-8 encoding and try again."
        ) from error
