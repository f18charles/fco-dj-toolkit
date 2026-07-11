from __future__ import annotations

from common.querysets import BaseQuerySet


class SocialAccountQuerySet(BaseQuerySet):
    """
    QuerySet for social authentication account queries.
    """

    def for_provider(self, provider: str) -> SocialAccountQuerySet:
        """Filter social accounts for a specific provider."""
        return self.filter(provider=provider.lower())
