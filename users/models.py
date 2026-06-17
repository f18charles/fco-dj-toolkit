"""
Custom User model for the fco-dj-kit `users` module.

Consuming projects must set:

    AUTH_USER_MODEL = "users.User"

in their Django settings (before the first migration is applied).
"""
from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.managers import UserManager
from users.validators import validate_avatar_image


def avatar_upload_path(instance: "User", filename: str) -> str:
    """Build a per-user upload path for avatar images, e.g. avatars/<uuid>/avatar.png."""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "img"
    return f"avatars/{instance.pk}/avatar.{extension}"


class User(AbstractUser):
    """
    Custom user model.

    Extends Django's `AbstractUser` with:
        * A UUID primary key instead of an auto-incrementing integer,
          so user IDs are non-sequential and safe to expose publicly.
        * A required, unique email address.
        * An optional avatar image.
        * `created_at` / `updated_at` audit timestamps.

    The username field is retained from `AbstractUser` as the
    `USERNAME_FIELD`; email is unique but supplementary unless the
    consuming project chooses to make it the login field.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    email = models.EmailField(
        _("email address"),
        unique=True,
    )
    avatar = models.ImageField(
        _("avatar"),
        upload_to=avatar_upload_path,
        blank=True,
        null=True,
        validators=[validate_avatar_image],
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    objects = UserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.email or self.username

    @property
    def full_name(self) -> str:
        """Return the user's full name, falling back to their username."""
        name = self.get_full_name()
        return name or self.username
