# File Converter

A small desktop app in Python that converts files between a fixed set of formats.
You choose an input file and an output folder, and the app lists only the target formats available for that file.

Project for the *Programowanie V* course.

## Supported conversions

| Group           | From | To   | How                     | Known limitations |
|-----------------|------|------|-------------------------|-------------------|
| Structured data | CSV  | JSON | Python standard library | All values become JSON strings; the first row must be a header with unique, non-empty names |
| Structured data | JSON | CSV  | Python standard library | Only an array of flat objects; nested objects/arrays are rejected; `null` becomes an empty cell |
| Text documents  | TXT  | DOCX | python-docx             | Plain text only; each line becomes a paragraph with the default style |
| Text documents  | DOCX | TXT  | python-docx             | Only paragraph text; tables, headers/footers, images and formatting are skipped |
| Office formats  | DOCX | PDF  | LibreOffice (headless)  | Layout may differ slightly from Microsoft Word |
| Office formats  | ODT  | PDF  | LibreOffice (headless)  | Same as above |
| Office formats  | DOCX | ODT  | LibreOffice (headless)  | Advanced Word features (macros, some styles) may not be preserved |
| Office formats  | ODT  | DOCX | LibreOffice (headless)  | Same as above |

Other pairs are not supported. The app does not show them.

## Requirements

- Python 3.11+ with Tkinter (included in the standard Windows and macOS installers).
- LibreOffice, needed only for the office formats:
  - Windows: `winget install TheDocumentFoundation.LibreOffice` or the installer from https://www.libreoffice.org/download/
  - Linux: `sudo apt install libreoffice` (and `sudo apt install python3-tk` for the GUI)
  - macOS: `brew install --cask libreoffice`

  The app looks for LibreOffice in the `LIBREOFFICE_PATH` environment variable, in `PATH` and in the default install folders.
  If it is installed elsewhere, set `LIBREOFFICE_PATH` to the `soffice` executable.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS
pip install -r requirements.txt
```

## Usage

GUI:

```bash
python -m konwerter
```

Choose an input file and an output folder, pick a target format and click **Convert**.
**Supported formats** shows all available pairs.

Command line:

```bash
mkdir out
python -m konwerter.cli samples/people.csv .json -o out
python -m konwerter.cli samples/report.docx .pdf -o out --overwrite
```

Without `-o` the result is saved next to the input file.
The output folder must already exist.

The `samples/` folder has example input files, including invalid ones for testing errors.
They are described in [TESTS.md](TESTS.md).

## How it works

```
konwerter/
  registry.py       registry of conversion pairs: (".csv", ".json") -> function
  service.py        request validation, overwrite policy, running the converter, logging
  errors.py         error types shown to the user
  converters/       one module per format group
  gui.py            Tkinter/ttk window
  cli.py            command-line interface
```

Each converter is a plain function `(source, target) -> None` registered with a decorator:

```python
@converter(".csv", ".json")
def csv_to_json(source: Path, target: Path) -> None:
    ...
```

When a file is selected, the GUI asks the registry for the available target formats.
Before a conversion runs, `service.py` checks the input file, the format pair, the output folder and any name conflict.
An existing file is overwritten only after confirmation.
The conversion runs in a background thread, so the window stays responsive.
Errors are shown as short messages that say what to do next, and they are written to `konwerter.log`.

To add a new conversion, write one decorated function in `converters/`. The GUI does not need any changes.

### Format details

- **CSV ↔ JSON:** UTF-8 input with or without BOM. The first CSV row is the header, and the delimiter `,` or `;` is detected automatically.
  JSON must be an array of flat objects, for example `[{"name": "Anna", "city": "Kraków"}]`.
  Column order is preserved. When objects have different keys, the columns are all keys in order of first appearance.
  CSV is written in UTF-8 with BOM, so Excel shows Polish characters correctly.
- **TXT ↔ DOCX:** TXT must be UTF-8. Each line of text is one paragraph, and empty lines are kept.
- **Office formats:** LibreOffice runs in headless mode with a temporary profile, so it also works while LibreOffice is open.
  The process has a 120-second timeout, and its exit code and output file are checked.

## Known limitations

- Complex formatting, embedded charts, footnotes, macros and identical page layout are not preserved.
- Text input (CSV, JSON, TXT) must be UTF-8. Other encodings are reported as an error.
- Only the pairs listed above are supported. There is no chaining (for example CSV → PDF).
- The output file always gets the input file name with the new extension.

## Tests

```bash
python -m pytest
```

Tests that need LibreOffice are skipped if it is not installed.
The test report and the manual test matrix are in [TESTS.md](TESTS.md).

## Sources and libraries

- [python-docx](https://python-docx.readthedocs.io/): reading and writing DOCX
- [LibreOffice command-line parameters](https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html): headless conversion
- [tkinter](https://docs.python.org/3/library/tkinter.html) and [tkinter.filedialog](https://docs.python.org/3/library/dialog.html): GUI
- [subprocess](https://docs.python.org/3/library/subprocess.html): running LibreOffice safely
- [csv](https://docs.python.org/3/library/csv.html), [json](https://docs.python.org/3/library/json.html), [pathlib](https://docs.python.org/3/library/pathlib.html): standard library
- [pytest](https://docs.pytest.org/): automated tests

## Author

Maksym Bielousov, student ID 106149, group 4
