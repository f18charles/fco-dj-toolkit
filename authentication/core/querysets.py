from __future__ import annotations

from common.querysets import BaseQuerySet


class LoginAttemptQuerySet(BaseQuerySet):
    """
    QuerySet for custom operations on LoginAttempt model.
    """

    def failed(self) -> LoginAttemptQuerySet:
        """Filter only failed login attempts."""
        return self.filter(was_successful=False)

    def successful(self) -> LoginAttemptQuerySet:
        """Filter only successful login attempts."""
        return self.filter(was_successful=True)

    def for_identifier(self, identifier: str) -> LoginAttemptQuerySet:
        """Filter attempts matching the identifier (case-insensitive)."""
        return self.filter(identifier__iexact=identifier.strip())
