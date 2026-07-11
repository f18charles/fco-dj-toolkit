from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import UUIDModel, TimestampedModel
from authentication.auth_methods.oauth2.managers import SocialAccountManager


class SocialAccount(UUIDModel, TimestampedModel):
    """
    Links a local User instance to a remote OAuth2 identity (e.g., Google or GitHub).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_accounts",
        verbose_name=_("user"),
    )
    provider = models.CharField(
        _("provider"),
        max_length=50,
        help_text=_("The OAuth2 provider name (e.g., 'google', 'github')."),
    )
    provider_user_id = models.CharField(
        _("provider user ID"),
        max_length=255,
        help_text=_("The unique user ID returned by the remote provider."),
    )

    objects = SocialAccountManager()

    class Meta:
        verbose_name = _("social account")
        verbose_name_plural = _("social accounts")
        unique_together = (("provider", "provider_user_id"),)

    def __str__(self) -> str:
        return f"{self.user} linked to {self.provider} ({self.provider_user_id})"
