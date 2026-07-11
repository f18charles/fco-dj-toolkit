from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import UUIDModel, TimestampedModel
from authentication.core.managers import LoginAttemptManager
from authentication.auth_methods.oauth2.models import SocialAccount


class LoginAttempt(UUIDModel, TimestampedModel):
    """
    Tracks both successful and failed authentication attempts.
    Used for lockout, analytics, and security auditing.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_attempts",
        verbose_name=_("user"),
    )
    identifier = models.CharField(
        _("identifier"),
        max_length=255,
        help_text=_("The username or email typed by the user."),
    )
    ip_address = models.GenericIPAddressField(
        _("IP address"),
        null=True,
        blank=True,
    )
    user_agent = models.CharField(
        _("user agent"),
        max_length=512,
        blank=True,
        default="",
    )
    was_successful = models.BooleanField(
        _("was successful"),
        db_index=True,
    )
    failure_reason = models.CharField(
        _("failure reason"),
        max_length=255,
        blank=True,
        default="",
    )

    objects = LoginAttemptManager()

    class Meta:
        verbose_name = _("login attempt")
        verbose_name_plural = _("login attempts")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["identifier", "created_at"]),
            models.Index(fields=["ip_address", "created_at"]),
        ]

    def __str__(self) -> str:
        status = "Success" if self.was_successful else f"Fail ({self.failure_reason})"
        return f"LoginAttempt: {self.identifier} - {status} at {self.created_at}"
