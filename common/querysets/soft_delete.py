"""
Soft-delete-aware queryset that also inherits ``BaseQuerySet``.

This module re-exports ``SoftDeleteQuerySet`` from
``common.mixins.soft_delete_mixin`` for backward compatibility and
additionally provides ``TimestampedSoftDeleteQuerySet``, which
combines soft-delete filtering with the timestamp-aware helpers from
``BaseQuerySet``.

Prefer ``TimestampedSoftDeleteQuerySet`` for models that compose both
``SoftDeleteMixin`` and ``TimestampMixin``.
"""
from __future__ import annotations

from common.mixins.soft_delete_mixin import SoftDeleteQuerySet
from common.querysets.base import BaseQuerySet


class TimestampedSoftDeleteQuerySet(BaseQuerySet, SoftDeleteQuerySet):
    """
    QuerySet for models that use both ``SoftDeleteMixin`` and
    ``TimestampMixin``.

    Inherits:
        * ``active()`` / ``deleted()`` from ``SoftDeleteQuerySet``
        * ``created_since()`` / ``updated_since()`` / ``newest()`` /
          ``oldest()`` / ``recently_updated()`` from ``BaseQuerySet``
        * Soft-delete ``delete()`` / ``hard_delete()`` override

    Example usage in a model::

        class Article(UUIDModel, TimestampedModel, SoftDeleteModel):
            objects = TimestampedSoftDeleteManager()
            all_objects = TimestampedSoftDeleteAllManager()

            class Meta:
                base_manager_name = "all_objects"
    """


__all__ = [
    "SoftDeleteQuerySet",
    "TimestampedSoftDeleteQuerySet",
]
