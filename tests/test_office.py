import subprocess
from pathlib import Path

import pytest

from konwerter.converters import office
from konwerter.converters.documents import docx_to_txt, txt_to_docx
from konwerter.errors import ExternalToolError, InvalidInputError, MissingDependencyError


def libreoffice_installed() -> bool:
    try:
        office.find_libreoffice()
    except MissingDependencyError:
        return False
    return True


needs_libreoffice = pytest.mark.skipif(not libreoffice_installed(), reason="LibreOffice is not installed")


@pytest.fixture
def docx_file(tmp_path):
    source = tmp_path / "in.txt"
    source.write_text("Zażółć gęślą jaźń\nDrugi akapit\n", encoding="utf-8")
    target = tmp_path / "doc.docx"
    txt_to_docx(source, target)
    return target


def test_wrong_libreoffice_path_in_config_is_reported(tmp_path, monkeypatch):
    monkeypatch.setenv(office.LIBREOFFICE_ENV, str(tmp_path / "missing" / "soffice.exe"))
    with pytest.raises(MissingDependencyError, match=office.LIBREOFFICE_ENV):
        office.find_libreoffice()


def test_libreoffice_not_installed_is_reported(monkeypatch):
    monkeypatch.delenv(office.LIBREOFFICE_ENV, raising=False)
    monkeypatch.setattr(office.shutil, "which", lambda name: None)
    monkeypatch.setattr(office, "COMMON_PATHS", [])
    with pytest.raises(MissingDependencyError, match="libreoffice.org"):
        office.find_libreoffice()


@needs_libreoffice
def test_docx_to_pdf(docx_file, tmp_path):
    target = tmp_path / "doc.pdf"
    office.convert_with_libreoffice(docx_file, target)
    assert target.read_bytes().startswith(b"%PDF")


@needs_libreoffice
def test_docx_odt_docx_keeps_text(docx_file, tmp_path):
    office.convert_with_libreoffice(docx_file, tmp_path / "doc.odt")
    office.convert_with_libreoffice(tmp_path / "doc.odt", tmp_path / "back.docx")
    docx_to_txt(tmp_path / "back.docx", tmp_path / "back.txt")
    assert (tmp_path / "back.txt").read_text(encoding="utf-8") == "Zażółć gęślą jaźń\nDrugi akapit\n"


def test_damaged_docx_to_pdf_raises_controlled_error(tmp_path):
    source = tmp_path / "damaged.docx"
    source.write_text("not a zip package", encoding="utf-8")
    with pytest.raises(InvalidInputError, match="not a valid DOCX"):
        office.convert_with_libreoffice(source, tmp_path / "out.pdf")
    assert not (tmp_path / "out.pdf").exists()


def test_libreoffice_failure_exit_code_is_reported(docx_file, tmp_path, monkeypatch):
    monkeypatch.setattr(office, "find_libreoffice", lambda: Path("soffice"))
    failed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="boom")
    monkeypatch.setattr(office.subprocess, "run", lambda *args, **kwargs: failed)
    with pytest.raises(ExternalToolError, match="exit code 1: boom"):
        office.convert_with_libreoffice(docx_file, tmp_path / "out.pdf")
