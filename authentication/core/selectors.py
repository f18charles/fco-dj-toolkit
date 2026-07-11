from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from authentication.core.models import LoginAttempt

User = get_user_model()


def get_login_history(user: User, *, limit: int = 50) -> QuerySet[LoginAttempt]:
    """
    Retrieve login history for a specific user, ordered by most recent first.
    """
    return LoginAttempt.objects.filter(user=user).order_by("-created_at")[:limit]


def get_recent_failed_attempts(identifier: str, *, limit: int = 50) -> QuerySet[LoginAttempt]:
    """
    Retrieve recent failed login attempts for a specific identifier, ordered by most recent first.
    """
    return LoginAttempt.objects.for_identifier(identifier).failed().order_by("-created_at")[:limit]
