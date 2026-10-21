import pytest

from konwerter.errors import InvalidInputError, OutputExistsError, UnsupportedConversionError
from konwerter.service import ConversionRequest, execute


@pytest.fixture
def csv_file(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("a,b\n1,2\n", encoding="utf-8")
    return path


def test_validate_missing_input_file(tmp_path):
    request = ConversionRequest(tmp_path / "missing.csv", ".json", tmp_path)
    with pytest.raises(InvalidInputError, match="not found"):
        request.validate()


def test_validate_missing_output_dir(csv_file, tmp_path):
    request = ConversionRequest(csv_file, ".json", tmp_path / "no_such_dir")
    with pytest.raises(InvalidInputError, match="Output folder not found"):
        request.validate()


def test_validate_unsupported_pair(csv_file, tmp_path):
    request = ConversionRequest(csv_file, ".pdf", tmp_path)
    with pytest.raises(UnsupportedConversionError):
        request.validate()


def test_validate_empty_target_format(csv_file, tmp_path):
    with pytest.raises(InvalidInputError, match="No target format"):
        ConversionRequest(csv_file, "", tmp_path).validate()


def test_target_format_is_normalized(csv_file, tmp_path):
    assert ConversionRequest(csv_file, "JSON", tmp_path).output_path == tmp_path / "data.json"


def test_existing_output_requires_overwrite(csv_file, tmp_path):
    existing = tmp_path / "data.json"
    existing.write_text("old", encoding="utf-8")
    request = ConversionRequest(csv_file, ".json", tmp_path)

    with pytest.raises(OutputExistsError):
        execute(request)
    assert existing.read_text(encoding="utf-8") == "old"

    assert execute(request, overwrite=True) == existing
    assert existing.read_text(encoding="utf-8") != "old"
