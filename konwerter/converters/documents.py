"""Text documents: TXT <-> DOCX (python-docx).

Every TXT line becomes one DOCX paragraph and vice versa, so the conversion is symmetric.
Only plain text is transferred: tables, headers/footers, images and formatting are skipped.
"""

from pathlib import Path
from types import ModuleType
from zipfile import BadZipFile

from konwerter.converters.common import read_utf8
from konwerter.errors import InvalidInputError, MissingDependencyError
from konwerter.registry import converter


@converter(".txt", ".docx")
def txt_to_docx(source: Path, target: Path) -> None:
    docx = _import_docx()
    document = docx.Document()
    for line in read_utf8(source).splitlines():
        document.add_paragraph(line)
    document.save(target)


@converter(".docx", ".txt")
def docx_to_txt(source: Path, target: Path) -> None:
    docx = _import_docx()
    try:
        document = docx.Document(source)
    except (BadZipFile, KeyError, docx.opc.exceptions.PackageNotFoundError) as error:
        raise InvalidInputError(
            f"{source.name} is not a valid DOCX file. Check that it opens in a word processor."
        ) from error
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    target.write_text(text + "\n", encoding="utf-8")


def _import_docx() -> ModuleType:
    try:
        import docx
        import docx.opc.exceptions
    except ImportError as error:
        raise MissingDependencyError(
            "python-docx is not installed. Run: pip install -r requirements.txt"
        ) from error
    return docx
