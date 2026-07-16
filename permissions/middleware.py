import logging
import threading
from typing import Any, Callable
from django.http import HttpRequest, HttpResponse

from permissions.signals import permission_checked

logger = logging.getLogger(__name__)
_thread_locals = threading.local()


def _permission_checked_receiver(
    sender: Any, user: Any, codename: str, result: bool, **kwargs: Any
) -> None:
    """
    Signal receiver that logs permission checks to python logging system.
    """
    if logger.isEnabledFor(logging.DEBUG):
        path = getattr(_thread_locals, "path", "unknown")
        user_str = str(user) if user else "Anonymous"
        logger.debug(
            f"Permission check: codename={codename}, result={result}, user={user_str}, path={path}"
        )


# Connect the receiver to the permission_checked signal
permission_checked.connect(_permission_checked_receiver)


class PermissionAuditMiddleware:
    """
    Logs every permission check (codename, result, user, path) to Python's
    logging system at DEBUG level. Connects to the permission_checked signal.

    To enable, add to MIDDLEWARE after AuthenticationMiddleware:
        "permissions.middleware.PermissionAuditMiddleware"

    Useful in development to trace which checks are happening per request.
    Has negligible overhead when Django's logging level is above DEBUG.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Set the current request path in thread-local storage
        _thread_locals.path = request.path
        try:
            response = self.get_response(request)
            return response
        finally:
            # Clean up the thread-local storage
            if hasattr(_thread_locals, "path"):
                del _thread_locals.path
