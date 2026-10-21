"""Registry of conversion directions: (source extension, target extension) -> converter function."""

from collections.abc import Callable
from pathlib import Path

Converter = Callable[[Path, Path], None]

REGISTRY: dict[tuple[str, str], Converter] = {}


def converter(source: str, target: str) -> Callable[[Converter], Converter]:
    """Decorator registering a single conversion direction, e.g. @converter(".csv", ".json")."""

    def register(func: Converter) -> Converter:
        REGISTRY[(source.lower(), target.lower())] = func
        return func

    return register


def available_targets(source: Path) -> list[str]:
    """Target extensions available for the given source file."""
    suffix = source.suffix.lower()
    return sorted(target for (src, target) in REGISTRY if src == suffix)


def supported_pairs() -> list[tuple[str, str]]:
    """All registered (source, target) pairs, sorted."""
    return sorted(REGISTRY)
