"""
Custom exceptions for the users module.

Services and selectors raise these instead of letting Django's
`DoesNotExist` / `IntegrityError` leak out, so callers (views, other
modules, management commands) can depend on a stable, module-owned
exception hierarchy instead of ORM internals.
"""


class UserModuleError(Exception):
    """Base class for all exceptions raised by the users module."""


class UserNotFoundError(UserModuleError):
    """Raised when a user lookup by id/email/etc. fails."""


class EmailAlreadyExistsError(UserModuleError):
    """Raised when attempting to set an email already used by another user."""


class InvalidUserStateError(UserModuleError):
    """Raised when an operation is attempted on a user in an invalid state."""


class UserAlreadyActiveError(InvalidUserStateError):
    """Raised when attempting to activate a user that is already active."""


class UserAlreadyInactiveError(InvalidUserStateError):
    """Raised when attempting to deactivate a user that is already inactive."""
