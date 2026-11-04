"""Conversion request validation and execution, independent of any user interface."""

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path

from konwerter import converters  # noqa: F401  (importing registers all converters)
from konwerter.errors import ConversionError, InvalidInputError, OutputExistsError, UnsupportedConversionError
from konwerter.registry import REGISTRY, supported_pairs

LOG_FILE = "konwerter.log"

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(
        filename=LOG_FILE,
        encoding="utf-8",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@dataclass(frozen=True)
class ConversionRequest:
    source: Path
    target_format: str
    output_dir: Path

    @property
    def target_suffix(self) -> str:
        """Target format normalized to a lowercase extension with a dot, e.g. 'JSON' -> '.json'."""
        suffix = self.target_format.strip().lower()
        return suffix if suffix.startswith(".") else f".{suffix}"

    @property
    def key(self) -> tuple[str, str]:
        return self.source.suffix.lower(), self.target_suffix

    @property
    def output_path(self) -> Path:
        return self.output_dir / f"{self.source.stem}{self.target_suffix}"

    def validate(self, overwrite: bool = False) -> None:
        if not self.target_format.strip():
            raise InvalidInputError("No target format selected. Choose a target format.")
        if not self.source.is_file():
            raise InvalidInputError(f"Input file not found: {self.source}. Choose an existing file.")
        if self.key not in REGISTRY:
            raise UnsupportedConversionError(
                f"Conversion {self.key[0]} -> {self.key[1]} is not supported. "
                f"Supported pairs: {_format_pairs()}."
            )
        if not self.output_dir.is_dir():
            raise InvalidInputError(f"Output folder not found: {self.output_dir}. Choose an existing folder.")
        if not os.access(self.output_dir, os.W_OK):
            raise InvalidInputError(f"No write permission for {self.output_dir}. Choose another output folder.")
        if self.output_path.exists() and not overwrite:
            raise OutputExistsError(
                f"File {self.output_path.name} already exists in {self.output_dir}. "
                "Allow overwriting or choose another folder."
            )


def execute(request: ConversionRequest, overwrite: bool = False) -> Path:
    """Validate the request, run the matching converter and return the path of the created file."""
    request.validate(overwrite)
    target = request.output_path
    convert = REGISTRY[request.key]
    started = time.perf_counter()
    try:
        convert(request.source, target)
    except ConversionError as error:
        logger.warning("Conversion failed: %s -> %s: %s", request.source, target, error)
        raise
    except Exception:
        logger.exception("Unexpected error: %s -> %s", request.source, target)
        raise
    logger.info("Converted %s -> %s in %.2f s", request.source, target, time.perf_counter() - started)
    return target


def _format_pairs() -> str:
    return ", ".join(f"{src} -> {dst}" for src, dst in supported_pairs())
