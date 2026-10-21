"""Structured data: CSV <-> JSON.

CSV: UTF-8 (BOM optional), first row is the header, delimiter ',' or ';' (auto-detected).
JSON: an array of flat objects; key order = column order. All CSV values become JSON strings.
"""

import csv
import io
import json
from pathlib import Path

from konwerter.converters.common import read_utf8
from konwerter.errors import InvalidInputError
from konwerter.registry import converter

# BOM lets Excel display Polish characters correctly; readers using utf-8-sig ignore it.
CSV_OUTPUT_ENCODING = "utf-8-sig"


@converter(".csv", ".json")
def csv_to_json(source: Path, target: Path) -> None:
    records = _read_csv(source)
    target.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


@converter(".json", ".csv")
def json_to_csv(source: Path, target: Path) -> None:
    records = _read_json_records(source)
    columns = list(dict.fromkeys(key for record in records for key in record))
    with target.open("w", encoding=CSV_OUTPUT_ENCODING, newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, restval="")
        writer.writeheader()
        writer.writerows({key: _to_cell(value) for key, value in record.items()} for record in records)


def _read_csv(path: Path) -> list[dict[str, str]]:
    text = read_utf8(path)
    if not text.strip():
        raise InvalidInputError(f"{path.name} is empty. Choose a CSV file with a header row.")

    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;")
    except csv.Error:
        dialect = csv.excel  # single column or ambiguous sample: fall back to commas

    reader = csv.reader(io.StringIO(text, newline=""), dialect)
    try:
        header = next(reader)
        _check_header(header, path)
        records = []
        for row in reader:
            if not row:
                continue  # skip blank lines
            if len(row) != len(header):
                raise InvalidInputError(
                    f"{path.name}, line {reader.line_num}: {len(row)} values, expected {len(header)}. "
                    "Fix the row so it matches the header."
                )
            records.append(dict(zip(header, row)))
    except csv.Error as error:
        raise InvalidInputError(f"{path.name} is not a valid CSV file: {error}.") from error

    if not records:
        raise InvalidInputError(f"{path.name} has a header but no data rows. Add at least one row.")
    return records


def _check_header(header: list[str], path: Path) -> None:
    if any(not name.strip() for name in header):
        raise InvalidInputError(f"{path.name}: the header contains an empty column name. Name every column.")
    duplicates = sorted({name for name in header if header.count(name) > 1})
    if duplicates:
        raise InvalidInputError(f"{path.name}: duplicate column names {duplicates}. Make column names unique.")


def _read_json_records(path: Path) -> list[dict]:
    try:
        data = json.loads(read_utf8(path))
    except json.JSONDecodeError as error:
        raise InvalidInputError(
            f"{path.name} is not valid JSON (line {error.lineno}, column {error.colno}: {error.msg}). "
            "Fix the file and try again."
        ) from error

    if not isinstance(data, list) or not all(isinstance(record, dict) for record in data):
        raise InvalidInputError(
            f'{path.name} must contain an array of objects, e.g. [{{"name": "Anna", "city": "Kraków"}}].'
        )
    if not data:
        raise InvalidInputError(f"{path.name} contains an empty array. Add at least one object.")

    for number, record in enumerate(data, start=1):
        for key, value in record.items():
            if isinstance(value, (dict, list)):
                raise InvalidInputError(
                    f"{path.name}, object {number}, field '{key}': nested values are not supported. "
                    "Use only text, numbers, true/false or null."
                )
    return data


def _to_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value)  # numbers and booleans in JSON notation: 1.5, true
