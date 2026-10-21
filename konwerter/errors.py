"""Common error model. Every message states the cause and the next step for the user."""


class ConversionError(Exception):
    """Base class for all expected, user-facing conversion errors."""


class InvalidInputError(ConversionError):
    """Input is missing, empty, unreadable or has invalid content."""


class UnsupportedConversionError(ConversionError):
    """The requested source/target pair is not in the registry."""


class OutputExistsError(ConversionError):
    """The target file already exists and overwriting was not allowed."""


class MissingDependencyError(ConversionError):
    """A required library or external tool is not installed."""


class ExternalToolError(ConversionError):
    """An external tool failed, timed out or produced no output."""
