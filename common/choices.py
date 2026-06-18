from django.db import models
from django.utils.translation import gettext_lazy as _


class StatusChoices(models.TextChoices):
    """
    Standard state choices for entities.
    """
    ACTIVE = "ACTIVE", _("Active")
    INACTIVE = "INACTIVE", _("Inactive")
    DRAFT = "DRAFT", _("Draft")
    ARCHIVED = "ARCHIVED", _("Archived")


class VisibilityChoices(models.TextChoices):
    """
    Standard visibility choices for resources.
    """
    PUBLIC = "PUBLIC", _("Public")
    PRIVATE = "PRIVATE", _("Private")
    RESTRICTED = "RESTRICTED", _("Restricted")
