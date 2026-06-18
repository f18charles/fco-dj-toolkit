import re
from typing import Any, Sequence
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

# Username validator: 3-30 characters, letters, numbers, dots, underscores, and hyphens.
USERNAME_REGEX = r"^[a-zA-Z0-9_.-]{3,30}$"
validate_username = RegexValidator(
    regex=USERNAME_REGEX,
    message=_(
        "Username must be 3-30 characters and may only contain "
        "letters, numbers, dots, underscores, and hyphens."
    ),
    code="invalid_username",
)

# Slug validator: lowercase letters, numbers, hyphens, and underscores.
SLUG_REGEX = r"^[a-z0-9_-]+$"
validate_slug = RegexValidator(
    regex=SLUG_REGEX,
    message=_("Slug must contain only lowercase letters, numbers, hyphens, or underscores."),
    code="invalid_slug",
)

# Phone number validator: simple international format.
PHONE_REGEX = r"^\+?[1-9]\d{1,14}$"
validate_phone_number = RegexValidator(
    regex=PHONE_REGEX,
    message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."),
    code="invalid_phone_number",
)


@deconstructible
class FileExtensionValidator:
    """
    Validate that an uploaded file has a permitted extension.
    """

    def __init__(self, allowed_extensions: Sequence[str]):
        self.allowed_extensions = [ext.lower().lstrip(".") for ext in allowed_extensions]

    def __call__(self, file: Any) -> None:
        name = getattr(file, "name", "")
        if not name or "." not in name:
            raise ValidationError(
                _("File has no extension."),
                code="no_extension",
            )
        ext = name.rsplit(".", 1)[-1].lower()
        if ext not in self.allowed_extensions:
            raise ValidationError(
                _("File extension '%(extension)s' is not allowed. Allowed extensions: %(allowed)s."),
                code="invalid_extension",
                params={"extension": ext, "allowed": ", ".join(self.allowed_extensions)},
            )

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, FileExtensionValidator)
            and self.allowed_extensions == other.allowed_extensions
        )
