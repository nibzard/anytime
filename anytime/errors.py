"""Exception types for anytime inference."""


class AnytimeError(Exception):
    """Base exception for anytime errors."""


class AssumptionViolationError(AnytimeError):
    """Raised when data violates declared assumptions."""

    pass


class ConfigError(AnytimeError):
    """Raised when configuration is invalid."""

    pass
