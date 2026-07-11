from __future__ import annotations

from typing import Any
from common.querysets import BaseQuerySet


class UserSessionQuerySet(BaseQuerySet):
    """
    QuerySet for operations on UserSession model.
    """

    def active(self) -> UserSessionQuerySet:
        """Filter only active sessions."""
        return self.filter(is_active=True)

    def for_user(self, user: Any) -> UserSessionQuerySet:
        """Filter sessions for a specific user."""
        return self.filter(user=user)
