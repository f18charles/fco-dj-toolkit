from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_password_strength(password: str) -> None:
    """
    Validate that a password meets strength requirements:
    - Minimum length of 10 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character

    Raises:
        ValidationError: listing all unmet requirements.
    """
    errors = []

    if len(password) < 10:
        errors.append(_("Password must be at least 10 characters long."))
    if not re.search(r"[A-Z]", password):
        errors.append(_("Password must contain at least one uppercase letter."))
    if not re.search(r"[a-z]", password):
        errors.append(_("Password must contain at least one lowercase letter."))
    if not re.search(r"\d", password):
        errors.append(_("Password must contain at least one digit."))
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append(_("Password must contain at least one special character (e.g., !@#$%^&*)."))

    if errors:
        raise ValidationError(errors, code="password_strength")
