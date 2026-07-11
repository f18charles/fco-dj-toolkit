from __future__ import annotations

from common.managers import BaseManager
from authentication.core.querysets import LoginAttemptQuerySet


class LoginAttemptManager(BaseManager):
    """
    Manager for the LoginAttempt model, wrapping LoginAttemptQuerySet.
    """

    def get_queryset(self) -> LoginAttemptQuerySet:
        return LoginAttemptQuerySet(self.model, using=self._db)

    def failed(self) -> LoginAttemptQuerySet:
        return self.get_queryset().failed()

    def successful(self) -> LoginAttemptQuerySet:
        return self.get_queryset().successful()

    def for_identifier(self, identifier: str) -> LoginAttemptQuerySet:
        return self.get_queryset().for_identifier(identifier)
