from pathlib import Path

from konwerter import service  # noqa: F401  (fills the registry)
from konwerter.registry import available_targets, supported_pairs


def test_available_targets_for_csv():
    assert available_targets(Path("data.csv")) == [".json"]


def test_available_targets_for_docx():
    assert available_targets(Path("report.docx")) == [".odt", ".pdf", ".txt"]


def test_available_targets_ignores_extension_case():
    assert available_targets(Path("DATA.JSON")) == [".csv"]


def test_available_targets_for_unknown_extension_is_empty():
    assert available_targets(Path("image.png")) == []


def test_supported_pairs_contains_structured_group():
    assert {(".csv", ".json"), (".json", ".csv")} <= set(supported_pairs())
