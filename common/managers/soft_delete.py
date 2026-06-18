"""
Soft-delete managers that use ``TimestampedSoftDeleteQuerySet``.

These complement the simpler ``SoftDeleteManager`` / ``SoftDeleteAllManager``
in ``common.mixins`` by also exposing the timestamp-aware methods from
``BaseQuerySet``.  Use these on models that compose all three mixins:

    class Article(UUIDModel, TimestampedModel, SoftDeleteModel):
        objects = TimestampedSoftDeleteManager()
        all_objects = TimestampedSoftDeleteAllManager()

        class Meta:
            base_manager_name = "all_objects"
"""
from __future__ import annotations

import datetime

from django.db import models

from common.querysets.soft_delete import TimestampedSoftDeleteQuerySet


class _TimestampedSoftDeleteManagerBase(models.Manager):
    """Shared proxy helpers for both soft-delete manager variants."""

    # Timestamp proxies ------------------------------------------------
    def created_since(self, dt: datetime.datetime) -> TimestampedSoftDeleteQuerySet:
        return self.get_queryset().created_since(dt)

    def updated_since(self, dt: datetime.datetime) -> TimestampedSoftDeleteQuerySet:
        return self.get_queryset().updated_since(dt)

    def created_in_last(self, **kw) -> TimestampedSoftDeleteQuerySet:
        return self.get_queryset().created_in_last(**kw)

    def updated_in_last(self, **kw) -> TimestampedSoftDeleteQuerySet:
        return self.get_queryset().updated_in_last(**kw)

    def newest(self) -> TimestampedSoftDeleteQuerySet:
        return self.get_queryset().newest()

    def oldest(self) -> TimestampedSoftDeleteQuerySet:
        return self.get_queryset().oldest()

    def recently_updated(self) -> TimestampedSoftDeleteQuerySet:
        return self.get_queryset().recently_updated()

    # Soft-delete proxies -----------------------------------------------
    def active(self) -> TimestampedSoftDeleteQuerySet:
        return self.get_queryset().active()

    def deleted(self) -> TimestampedSoftDeleteQuerySet:
        return self.get_queryset().deleted()


class TimestampedSoftDeleteManager(_TimestampedSoftDeleteManagerBase):
    """
    Default manager for timestamped soft-delete models.

    Returns only active (non-deleted) records.
    """

    def get_queryset(self) -> TimestampedSoftDeleteQuerySet:
        return TimestampedSoftDeleteQuerySet(self.model, using=self._db).active()


class TimestampedSoftDeleteAllManager(_TimestampedSoftDeleteManagerBase):
    """
    Unfiltered manager — returns all records including soft-deleted ones.

    Assign to ``all_objects`` and declare as ``base_manager_name`` so
    Django's internal related-object lookups work across the full dataset.
    """

    def get_queryset(self) -> TimestampedSoftDeleteQuerySet:
        return TimestampedSoftDeleteQuerySet(self.model, using=self._db)


__all__ = [
    "TimestampedSoftDeleteManager",
    "TimestampedSoftDeleteAllManager",
]
