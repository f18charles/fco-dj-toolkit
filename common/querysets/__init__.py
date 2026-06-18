"""
common.querysets
================

Re-usable Django QuerySet classes for fco-dj-kit models.

    from common.querysets import BaseQuerySet, TimestampedSoftDeleteQuerySet
"""
from common.querysets.base import BaseQuerySet
from common.querysets.soft_delete import SoftDeleteQuerySet, TimestampedSoftDeleteQuerySet

__all__ = [
    "BaseQuerySet",
    "SoftDeleteQuerySet",
    "TimestampedSoftDeleteQuerySet",
]
