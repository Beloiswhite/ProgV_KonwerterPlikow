"""Entry point: python -m konwerter starts the GUI."""

from konwerter.gui import run
from konwerter.service import configure_logging

configure_logging()
run()
