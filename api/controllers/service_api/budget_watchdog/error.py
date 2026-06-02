"""Error types for the Budget Watchdog."""

from typing import TypeVar

T = TypeVar("T")


class WatchdogError(Exception):
    """Base error for all budget watchdog operations."""

    pass


class BudgetExceededError(WatchdogError):
    """Raised when a budget limit has been reached or exceeded."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class DowngradeUnavailableError(WatchdogError):
    """Raised when no cheaper model is available for downgrade."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        super().__init__(f"No downgrade available for model '{model_name}'")


class MemberQuotaExceededError(WatchdogError):
    """Raised when a team member's quota has been exceeded."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidConfigError(WatchdogError):
    """Raised when the budget watchdog is misconfigured."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AlertStoreError(WatchdogError):
    """Raised when an alert storage operation fails."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


# Convenience type alias
WatchdogResult = T  # Type alias for better ergonomics
