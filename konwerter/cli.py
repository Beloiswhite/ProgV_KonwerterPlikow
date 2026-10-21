"""Command-line entry point: python -m konwerter.cli <file> <target format> [-o DIR] [--overwrite]"""

import argparse
import sys
from pathlib import Path

from konwerter.errors import ConversionError
from konwerter.service import ConversionRequest, configure_logging, execute


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m konwerter.cli", description="Convert a file without the GUI.")
    parser.add_argument("source", type=Path, help="input file")
    parser.add_argument("target_format", help="target extension, e.g. .json")
    parser.add_argument("-o", "--output-dir", type=Path, help="output folder (default: input file's folder)")
    parser.add_argument("--overwrite", action="store_true", help="overwrite an existing output file")
    args = parser.parse_args(argv)

    configure_logging()
    request = ConversionRequest(args.source, args.target_format, args.output_dir or args.source.parent)
    try:
        result = execute(request, overwrite=args.overwrite)
    except ConversionError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Saved: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
