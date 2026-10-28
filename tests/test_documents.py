import sys

import pytest

from konwerter.converters.documents import docx_to_txt, txt_to_docx
from konwerter.errors import InvalidInputError, MissingDependencyError


def test_txt_docx_txt_round_trip_keeps_lines_and_polish_chars(tmp_path):
    text = "Zażółć gęślą jaźń\n\nDrugi akapit — Łódź.\n"
    source = tmp_path / "in.txt"
    source.write_text(text, encoding="utf-8")

    txt_to_docx(source, tmp_path / "mid.docx")
    docx_to_txt(tmp_path / "mid.docx", tmp_path / "back.txt")

    assert (tmp_path / "back.txt").read_text(encoding="utf-8") == text


def test_damaged_docx_raises_controlled_error(tmp_path):
    source = tmp_path / "damaged.docx"
    source.write_text("not a zip package", encoding="utf-8")
    with pytest.raises(InvalidInputError, match="not a valid DOCX"):
        docx_to_txt(source, tmp_path / "out.txt")


def test_missing_python_docx_is_reported(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "docx", None)  # makes "import docx" fail
    source = tmp_path / "in.txt"
    source.write_text("text", encoding="utf-8")
    with pytest.raises(MissingDependencyError, match="pip install"):
        txt_to_docx(source, tmp_path / "out.docx")
