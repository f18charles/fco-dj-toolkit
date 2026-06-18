from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserTrackingMixin(models.Model):
    """
    Model mixin adding 'created_by' and 'updated_by' relationships.
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_created",
        null=True,
        blank=True,
        verbose_name=_("created by"),
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_updated",
        null=True,
        blank=True,
        verbose_name=_("updated by"),
    )

    class Meta:
        abstract = True
