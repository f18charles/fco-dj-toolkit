"""
Reusable validators for the users module.

These are kept independent of any particular model instance so they
can be reused from forms, serializers, services, or model field
validators alike.
"""
from __future__ import annotations

import re
from typing import Any

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.-]{3,30}$")

MAX_AVATAR_SIZE_MB = 5
ALLOWED_AVATAR_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def validate_username(value: str) -> None:
    """
    Validate a username against the module's username policy.

    Allowed: 3-30 characters, letters, numbers, dots, underscores, and
    hyphens.

    Raises:
        ValidationError: if the username does not match the policy.
    """
    if not value or not USERNAME_REGEX.match(value):
        raise ValidationError(
            _(
                "Username must be 3-30 characters and may only contain "
                "letters, numbers, dots, underscores, and hyphens."
            ),
            code="invalid_username",
        )


def validate_unique_email(email: str, model: Any, *, exclude_pk: Any = None) -> None:
    """
    Validate that no other user already has the given email.

    This is a model-agnostic check (takes the model as a parameter) so
    it can be reused with a swapped-in custom user model.

    Args:
        email: The email address to check.
        model: The user model class to query against.
        exclude_pk: Optional primary key to exclude from the check
            (used when validating an email change for an existing user).

    Raises:
        ValidationError: if the email is already in use.
    """
    queryset = model.objects.filter(email__iexact=email)
    if exclude_pk is not None:
        queryset = queryset.exclude(pk=exclude_pk)
    if queryset.exists():
        raise ValidationError(
            _("A user with this email already exists."),
            code="email_taken",
        )


def validate_avatar_image(file: Any) -> None:
    """
    Validate an uploaded avatar image.

    Checks the content type (must be JPEG/PNG/WEBP) and file size
    (must not exceed MAX_AVATAR_SIZE_MB). Intended for use both as a
    field validator (`ImageField(validators=[validate_avatar_image])`)
    and from form `clean_*` methods.

    Raises:
        ValidationError: if the file fails either check.
    """
    content_type = getattr(file, "content_type", None)
    if content_type and content_type not in ALLOWED_AVATAR_CONTENT_TYPES:
        raise ValidationError(
            _("Avatar must be a JPEG, PNG, or WEBP image."),
            code="invalid_avatar_type",
        )

    size = getattr(file, "size", None)
    if size and size > MAX_AVATAR_SIZE_MB * 1024 * 1024:
        raise ValidationError(
            _("Avatar file size must not exceed %(max)sMB."),
            code="avatar_too_large",
            params={"max": MAX_AVATAR_SIZE_MB},
        )
