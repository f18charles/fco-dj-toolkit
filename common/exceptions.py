from typing import Any, Dict, List, Optional, Union


class FcoKitException(Exception):
    """
    Base exception for all FCO Django Kit exceptions.
    """

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.code = code or "error"


class ValidationException(FcoKitException):
    """
    Raised when validation fails in the service or business logic layer.
    """

    def __init__(
        self,
        message: str,
        code: str = "validation_error",
        errors: Optional[Union[Dict[str, List[str]], List[str], Any]] = None,
    ):
        super().__init__(message, code)
        self.errors = errors or {}


class ServiceException(FcoKitException):
    """
    Raised when an operation in the service layer fails.
    """

    def __init__(self, message: str, code: str = "service_error"):
        super().__init__(message, code)


class NotFoundException(FcoKitException):
    """
    Raised when a requested resource is not found.
    """

    def __init__(self, message: str = "Resource not found", code: str = "not_found"):
        super().__init__(message, code)


class PermissionException(FcoKitException):
    """
    Raised when an action is not permitted.
    """

    def __init__(self, message: str = "Permission denied", code: str = "permission_denied"):
        super().__init__(message, code)
