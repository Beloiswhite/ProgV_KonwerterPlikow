# File Converter

A small desktop app in Python that converts files between a fixed set of formats.
You choose an input file and an output folder, and the app lists only the target formats available for that file.

Project for the *Programowanie V* course.

## Supported conversions

| Group           | From       | To          | How                    |
|-----------------|------------|-------------|------------------------|
| Structured data | CSV        | JSON        | Python standard library |
| Structured data | JSON       | CSV         | Python standard library |
| Text documents  | TXT        | DOCX        | python-docx            |
| Text documents  | DOCX       | TXT         | python-docx            |
| Office formats  | DOCX / ODT | PDF         | LibreOffice (headless) |
| Office formats  | DOCX       | ODT         | LibreOffice (headless) |
| Office formats  | ODT        | DOCX        | LibreOffice (headless) |

Other pairs are not supported. The app does not show them.

## Requirements

- Python 3.11+
- LibreOffice, needed only for the office formats. The app finds it in `PATH` or in the default install folder.
  You can also set the `LIBREOFFICE_PATH` environment variable to the `soffice` executable.

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

Command line:

```bash
python -m konwerter.cli samples/people.csv .json -o out
python -m konwerter.cli samples/report.docx .pdf -o out --overwrite
```

The `samples/` folder has example input files, including invalid ones for testing errors.

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
Errors are shown as short messages that say what to do next, and they are written to `konwerter.log`.

To add a new conversion, write one decorated function in `converters/`. The GUI does not need any changes.

### Format details

- **CSV ↔ JSON:** UTF-8 encoding. The first CSV row is the header, and the delimiter is `,` or `;`.
  JSON must be an array of flat objects. Column order is preserved.
- **TXT ↔ DOCX:** each line of text is one paragraph. Only text is transferred, without formatting, tables or images.
- **Office formats:** LibreOffice converts these in headless mode. The layout may differ slightly from the original.

## Tests

```bash
python -m pytest
```

Tests that need LibreOffice are skipped if it is not installed.
