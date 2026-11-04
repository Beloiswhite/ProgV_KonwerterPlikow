# Test report

Environment: Windows 11, Python 3.11, python-docx 1.2.0, LibreOffice 26.8.1, pytest 9.2.
The project was installed in a new virtual environment as described in [README.md](README.md).

## Automated tests

```bash
python -m pytest -v
```

Result: **33 passed**, 0 skipped. Tests that need LibreOffice are skipped when it is not installed.

| File | What it checks |
|------|----------------|
| `tests/test_registry.py` | `available_targets()` for CSV, JSON, DOCX, upper-case extensions and unknown extensions; list of supported pairs |
| `tests/test_service.py` | `validate()`: missing input file, missing output folder, unsupported pair, empty target format, format normalization; overwrite policy (existing file kept without `overwrite`, replaced with it) |
| `tests/test_structured.py` | CSV → JSON with Polish characters, empty values and column order; `;` delimiter; CSV → JSON → CSV round trip; JSON → CSV with different keys, `null` and booleans; invalid JSON (syntax, not an array, empty array, nested values); invalid CSV (empty, header only, duplicate columns, wrong number of values); non-UTF-8 file |
| `tests/test_documents.py` | TXT → DOCX → TXT round trip (Polish characters, empty lines); damaged DOCX; missing python-docx library |
| `tests/test_office.py` | Wrong `LIBREOFFICE_PATH`; LibreOffice not installed; LibreOffice non-zero exit code; damaged DOCX; DOCX → PDF; DOCX → ODT → DOCX keeps the text |

## Minimal test matrix

| # | Case | Input | Steps | Expected result | Actual result | Evidence |
|---|------|-------|-------|-----------------|---------------|----------|
| 1 | Valid file in each group | `samples/people.csv`, `samples/products.json`, `samples/letter.txt`, `samples/report.docx`, `samples/report.odt` | Convert each file to every available format (8 pairs) | A file is created and opens with the correct content | Pass: all 8 files were created and opened correctly | CLI run in a clean venv; `test_structured.py`, `test_documents.py`, `test_office.py` |
| 2 | Invalid or damaged file | `samples/broken.json`, `samples/damaged.docx` | Convert `broken.json` → CSV and `damaged.docx` → PDF / TXT | No crash; a clear message | Pass: `broken.json is not valid JSON (line 4, column 1: Expecting ',' delimiter). Fix the file and try again.` and `damaged.docx is not a valid DOCX file. Check that it opens in a word processor.` No output file is created | GUI, CLI; `test_invalid_json_raises_controlled_error`, `test_damaged_docx_*` |
| 3 | Unsupported pair | Any `.png` file; `samples/people.csv` | GUI: choose a `.png` file. CLI: `people.csv .pdf` | The option is not shown; no conversion is attempted | Pass: GUI shows an empty format list, **Convert** is disabled and the status says the type cannot be converted. CLI: `Conversion .csv -> .pdf is not supported. Supported pairs: …` | GUI; `test_validate_unsupported_pair` |
| 4 | LibreOffice or library missing | `samples/report.docx` | Set `LIBREOFFICE_PATH=C:\nope\soffice.exe` and convert to PDF | A controlled error with instructions | Pass: `LIBREOFFICE_PATH points to C:\nope\soffice.exe, which does not exist. Fix the variable or remove it to use auto-detection.` Without LibreOffice: `LibreOffice was not found. Install it from https://www.libreoffice.org/download/ or set LIBREOFFICE_PATH …` | CLI; `test_wrong_libreoffice_path_in_config_is_reported`, `test_libreoffice_not_installed_is_reported`, `test_missing_python_docx_is_reported` |
| 5 | Target file already exists | `samples/report.docx` → PDF twice | Convert the same file twice into the same folder | A question before overwriting | Pass: GUI asks `… already exists. Overwrite it?`. **Yes** replaces the file, **No** shows "Conversion cancelled." CLI refuses without `--overwrite` | GUI, CLI; `test_existing_output_requires_overwrite` |
| 6 | Polish characters and empty values | `samples/people.csv` | CSV → JSON → CSV, then compare with the input | Characters and data structure stay correct | Pass: `Zażółć`, `Gęślą-Jaźń`, `Łódź` are unchanged, empty cells stay empty, a value with a comma (`"Małgorzata, Maria"`) stays one cell, and the column order is the same | CLI; `test_csv_to_json_keeps_polish_chars_order_and_empty_values`, `test_csv_json_csv_round_trip` |

The application logs every conversion with its duration, and every error, to `konwerter.log`.

## Sample data

| File | Purpose | Expected result |
|------|---------|-----------------|
| `samples/people.csv` | CSV with Polish characters, empty cells and a quoted value with a comma | JSON array of 4 objects with keys `id, first_name, last_name, city, email`, where empty cells become `""` |
| `samples/products.json` | JSON with numbers, booleans, `null` and objects that have different keys | CSV with columns `name, price, in_stock, note, origin`. `null` and missing keys become empty cells, and booleans become `true`/`false` |
| `samples/broken.json` | JSON with a missing `}` | Error with the line and column number; no output file |
| `samples/letter.txt` | Letter with several paragraphs, empty lines and Polish characters | DOCX with one paragraph per line; converting it back to TXT gives the same text |
| `samples/report.docx` | Document with headings, bold/italic text and a table | PDF/ODT with the same content and layout. TXT contains the paragraph text without the table |
| `samples/report.odt` | The same document in ODT format | PDF/DOCX with the same content |
| `samples/damaged.docx` | Plain text file with a `.docx` extension | Error "not a valid DOCX file"; LibreOffice is not started |
