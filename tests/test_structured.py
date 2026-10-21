import csv
import json

import pytest

from konwerter.converters.structured import csv_to_json, json_to_csv
from konwerter.errors import InvalidInputError


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.reader(file))


def test_csv_to_json_keeps_polish_chars_order_and_empty_values(tmp_path):
    source = tmp_path / "in.csv"
    source.write_text("miasto,imię,uwagi\nŁódź,Zażółć,\nKraków,,brak\n", encoding="utf-8")
    target = tmp_path / "out.json"

    csv_to_json(source, target)

    records = json.loads(target.read_text(encoding="utf-8"))
    assert records == [
        {"miasto": "Łódź", "imię": "Zażółć", "uwagi": ""},
        {"miasto": "Kraków", "imię": "", "uwagi": "brak"},
    ]
    assert list(records[0]) == ["miasto", "imię", "uwagi"]


def test_csv_with_semicolon_delimiter(tmp_path):
    source = tmp_path / "in.csv"
    source.write_text("a;b\n1;2\n", encoding="utf-8")
    target = tmp_path / "out.json"

    csv_to_json(source, target)

    assert json.loads(target.read_text(encoding="utf-8")) == [{"a": "1", "b": "2"}]


def test_csv_json_csv_round_trip(tmp_path):
    original = tmp_path / "in.csv"
    original.write_text('id,name\n1,"Gęś, kura"\n2,\n', encoding="utf-8")

    csv_to_json(original, tmp_path / "mid.json")
    json_to_csv(tmp_path / "mid.json", tmp_path / "back.csv")

    assert read_csv(tmp_path / "back.csv") == [["id", "name"], ["1", "Gęś, kura"], ["2", ""]]


def test_json_to_csv_merges_keys_in_first_seen_order(tmp_path):
    source = tmp_path / "in.json"
    source.write_text(
        json.dumps([{"b": 1, "a": None}, {"a": "x", "c": True}], ensure_ascii=False), encoding="utf-8"
    )
    target = tmp_path / "out.csv"

    json_to_csv(source, target)

    assert read_csv(target) == [["b", "a", "c"], ["1", "", ""], ["", "x", "true"]]


@pytest.mark.parametrize(
    "content, message",
    [
        ('[{"a": 1}', "not valid JSON"),
        ('{"a": 1}', "array of objects"),
        ("[]", "empty array"),
        ('[{"a": {"b": 1}}]', "nested values"),
    ],
)
def test_invalid_json_raises_controlled_error(tmp_path, content, message):
    source = tmp_path / "in.json"
    source.write_text(content, encoding="utf-8")
    with pytest.raises(InvalidInputError, match=message):
        json_to_csv(source, tmp_path / "out.csv")
    assert not (tmp_path / "out.csv").exists()


@pytest.mark.parametrize(
    "content, message",
    [
        ("", "empty"),
        ("a,b\n", "no data rows"),
        ("a,a\n1,2\n", "duplicate"),
        ("a,b\n1,2,3\n", "line 2"),
    ],
)
def test_invalid_csv_raises_controlled_error(tmp_path, content, message):
    source = tmp_path / "in.csv"
    source.write_text(content, encoding="utf-8")
    with pytest.raises(InvalidInputError, match=message):
        csv_to_json(source, tmp_path / "out.json")


def test_non_utf8_file_raises_controlled_error(tmp_path):
    source = tmp_path / "in.csv"
    source.write_bytes("a\nŁódź\n".encode("cp1250"))
    with pytest.raises(InvalidInputError, match="UTF-8"):
        csv_to_json(source, tmp_path / "out.json")
