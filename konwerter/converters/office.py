"""Office formats via LibreOffice in headless mode: DOCX/ODT -> PDF, DOCX <-> ODT."""

import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from konwerter.errors import ExternalToolError, InvalidInputError, MissingDependencyError
from konwerter.registry import converter

LIBREOFFICE_ENV = "LIBREOFFICE_PATH"
TIMEOUT_SECONDS = 120

COMMON_PATHS = [
    Path("C:/Program Files/LibreOffice/program/soffice.exe"),
    Path("C:/Program Files (x86)/LibreOffice/program/soffice.exe"),
    Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
]


def find_libreoffice() -> Path:
    """Locate the soffice executable: LIBREOFFICE_PATH, then PATH, then default install folders."""
    configured = os.environ.get(LIBREOFFICE_ENV)
    if configured:
        path = Path(configured)
        if path.is_file():
            return path
        raise MissingDependencyError(
            f"{LIBREOFFICE_ENV} points to {path}, which does not exist. "
            "Fix the variable or remove it to use auto-detection."
        )

    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return Path(found)

    for path in COMMON_PATHS:
        if path.is_file():
            return path

    raise MissingDependencyError(
        "LibreOffice was not found. Install it from https://www.libreoffice.org/download/ "
        f"or set {LIBREOFFICE_ENV} to the path of the soffice executable."
    )


@converter(".docx", ".pdf")
@converter(".odt", ".pdf")
@converter(".docx", ".odt")
@converter(".odt", ".docx")
def convert_with_libreoffice(source: Path, target: Path) -> None:
    # DOCX and ODT are ZIP packages; LibreOffice would silently import anything else as plain text.
    if not zipfile.is_zipfile(source):
        raise InvalidInputError(
            f"{source.name} is not a valid {source.suffix.lstrip('.').upper()} file. "
            "Check that it opens in a word processor."
        )
    soffice = find_libreoffice()
    with tempfile.TemporaryDirectory() as tmp:
        work_dir = Path(tmp)
        command = [
            str(soffice),
            "--headless",
            "--norestore",
            # A private profile keeps the call independent of an already open LibreOffice window.
            f"-env:UserInstallation={(work_dir / 'profile').as_uri()}",
            "--convert-to", target.suffix.lstrip("."),
            "--outdir", str(work_dir),
            str(source),
        ]
        try:
            result = subprocess.run(
                command, capture_output=True, encoding="utf-8", errors="replace", timeout=TIMEOUT_SECONDS
            )
        except subprocess.TimeoutExpired as error:
            raise ExternalToolError(
                f"LibreOffice did not finish within {TIMEOUT_SECONDS} s. Try again with a smaller file."
            ) from error
        except OSError as error:
            raise MissingDependencyError(f"Cannot start LibreOffice ({soffice}): {error}.") from error

        if result.returncode != 0:
            details = result.stderr.strip() or "no details"
            raise ExternalToolError(f"LibreOffice failed with exit code {result.returncode}: {details}.")

        produced = work_dir / f"{source.stem}{target.suffix}"
        if not produced.is_file():
            raise ExternalToolError(
                f"LibreOffice could not convert {source.name}. Check that the file is not damaged."
            )
        shutil.move(produced, target)
