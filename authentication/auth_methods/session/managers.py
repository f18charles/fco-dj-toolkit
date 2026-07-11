from __future__ import annotations

from typing import Any
from common.managers import BaseManager
from authentication.auth_methods.session.querysets import UserSessionQuerySet


class UserSessionManager(BaseManager):
    """
    Manager for the UserSession model, wrapping UserSessionQuerySet.
    """

    def get_queryset(self) -> UserSessionQuerySet:
        return UserSessionQuerySet(self.model, using=self._db)

    def active(self) -> UserSessionQuerySet:
        return self.get_queryset().active()

    def for_user(self, user: Any) -> UserSessionQuerySet:
        return self.get_queryset().for_user(user)
