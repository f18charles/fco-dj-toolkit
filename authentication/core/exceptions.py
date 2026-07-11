from typing import Any, Optional
from common.exceptions import FcoKitException


class AuthenticationModuleError(FcoKitException):
    """
    Base exception class for all errors in the authentication module.
    """
    def __init__(self, message: str, code: str = "authentication_error"):
        super().__init__(message, code)


class InvalidCredentialsError(AuthenticationModuleError):
    """
    Raised when username/email and password validation fails.
    """
    def __init__(self, message: str = "Invalid credentials provided.", code: str = "invalid_credentials"):
        super().__init__(message, code)


class AccountLockedError(AuthenticationModuleError):
    """
    Raised when an account is temporarily locked out due to too many failed attempts.
    """
    def __init__(
        self,
        message: str = "Account temporarily locked out. Please try again later.",
        code: str = "account_locked",
        retry_after_seconds: int = 900,
    ):
        super().__init__(message, code)
        self.retry_after_seconds = retry_after_seconds


class AccountInactiveError(AuthenticationModuleError):
    """
    Raised when trying to authenticate an inactive user account.
    """
    def __init__(self, message: str = "Account is inactive.", code: str = "account_inactive"):
        super().__init__(message, code)


class EmailNotVerifiedError(AuthenticationModuleError):
    """
    Raised when an action requires a verified email address but the user has not verified it.
    """
    def __init__(self, message: str = "Email address has not been verified.", code: str = "email_not_verified"):
        super().__init__(message, code)


class EmailAlreadyVerifiedError(AuthenticationModuleError):
    """
    Raised when attempting to verify an email that is already verified.
    """
    def __init__(self, message: str = "Email address is already verified.", code: str = "email_already_verified"):
        super().__init__(message, code)


class InvalidTokenError(AuthenticationModuleError):
    """
    Raised when a reset or verification token is invalid or corrupt.
    """
    def __init__(self, message: str = "The token is invalid.", code: str = "invalid_token"):
        super().__init__(message, code)


class TokenExpiredError(AuthenticationModuleError):
    """
    Raised when a reset or verification token has expired.
    """
    def __init__(self, message: str = "The token has expired.", code: str = "token_expired"):
        super().__init__(message, code)


class SessionNotFoundError(AuthenticationModuleError):
    """
    Raised when a user session cannot be found.
    """
    def __init__(self, message: str = "Session not found.", code: str = "session_not_found"):
        super().__init__(message, code)


class TwoFactorRequiredError(AuthenticationModuleError):
    """
    Raised when 2FA validation is required before completing authentication.
    """
    def __init__(
        self,
        message: str = "Two-factor authentication is required.",
        code: str = "two_factor_required",
        challenge_id: Optional[str] = None,
    ):
        super().__init__(message, code)
        self.challenge_id = challenge_id
