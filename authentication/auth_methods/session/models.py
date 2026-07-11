from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import UUIDModel, TimestampedModel
from authentication.auth_methods.session.managers import UserSessionManager


class UserSession(UUIDModel, TimestampedModel):
    """
    Represents an active, authenticated HTTP session for a user.
    Integrates directly with Django's database-backed session engine or custom session management.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_sessions",
        verbose_name=_("user"),
    )
    session_key = models.CharField(
        _("session key"),
        max_length=40,
        unique=True,
        db_index=True,
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
    is_active = models.BooleanField(
        _("is active"),
        default=True,
        db_index=True,
    )
    last_activity = models.DateTimeField(
        _("last activity"),
        auto_now=True,
    )

    objects = UserSessionManager()

    class Meta:
        verbose_name = _("user session")
        verbose_name_plural = _("user sessions")
        ordering = ["-last_activity"]

    def __str__(self) -> str:
        return f"Session {self.session_key[:8]}... for {self.user}"

    def revoke(self) -> None:
        """
        Mark this session record as inactive and delete the underlying
        Django session object to invalidate it immediately.
        """
        self.is_active = False
        self.save(update_fields=["is_active"])

        # Delete the underlying django session row
        from django.contrib.sessions.models import Session
        Session.objects.filter(session_key=self.session_key).delete()
