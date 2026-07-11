from __future__ import annotations

from common.managers import BaseManager
from authentication.auth_methods.oauth2.querysets import SocialAccountQuerySet


class SocialAccountManager(BaseManager):
    """
    Manager for the SocialAccount model, wrapping SocialAccountQuerySet.
    """

    def get_queryset(self) -> SocialAccountQuerySet:
        return SocialAccountQuerySet(self.model, using=self._db)

    def for_provider(self, provider: str) -> SocialAccountQuerySet:
        return self.get_queryset().for_provider(provider)
