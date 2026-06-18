"""
Base QuerySet for the common module.

Provides chainable timestamp-aware filters that work for any model
that inherits ``TimestampMixin`` (i.e. has ``created_at`` /
``updated_at`` fields). More specialised querysets (e.g.
``SoftDeleteQuerySet``) live in ``common/mixins/`` and can inherit
from this class or be used independently.
"""
from __future__ import annotations

import datetime

from django.db import models
from django.utils import timezone


class BaseQuerySet(models.QuerySet):
    """
    Common queryset extensions available to all fco-dj-kit models.

    Designed to be used as a base for app-specific querysets:

        class ProductQuerySet(BaseQuerySet):
            def in_stock(self):
                return self.filter(stock__gt=0)

        class ProductManager(BaseManager):
            def get_queryset(self):
                return ProductQuerySet(self.model, using=self._db)
    """

    # ------------------------------------------------------------------
    # Timestamp filters (require TimestampMixin / created_at+updated_at)
    # ------------------------------------------------------------------

    def created_since(self, dt: datetime.datetime) -> "BaseQuerySet":
        """
        Return records created at or after ``dt``.

        Args:
            dt: A timezone-aware datetime object.
        """
        return self.filter(created_at__gte=dt)

    def updated_since(self, dt: datetime.datetime) -> "BaseQuerySet":
        """
        Return records updated at or after ``dt``.

        Args:
            dt: A timezone-aware datetime object.
        """
        return self.filter(updated_at__gte=dt)

    def created_in_last(self, **timedelta_kwargs) -> "BaseQuerySet":
        """
        Return records created within the last ``timedelta_kwargs``.

        Accepts the same keyword arguments as ``datetime.timedelta``:
        days, hours, minutes, seconds, etc.

        Example::

            Post.objects.created_in_last(days=7)
        """
        cutoff = timezone.now() - datetime.timedelta(**timedelta_kwargs)
        return self.created_since(cutoff)

    def updated_in_last(self, **timedelta_kwargs) -> "BaseQuerySet":
        """
        Return records updated within the last ``timedelta_kwargs``.

        Example::

            Post.objects.updated_in_last(hours=24)
        """
        cutoff = timezone.now() - datetime.timedelta(**timedelta_kwargs)
        return self.updated_since(cutoff)

    # ------------------------------------------------------------------
    # Ordering helpers
    # ------------------------------------------------------------------

    def newest(self) -> "BaseQuerySet":
        """Order by ``created_at`` descending (newest first)."""
        return self.order_by("-created_at")

    def oldest(self) -> "BaseQuerySet":
        """Order by ``created_at`` ascending (oldest first)."""
        return self.order_by("created_at")

    def recently_updated(self) -> "BaseQuerySet":
        """Order by ``updated_at`` descending."""
        return self.order_by("-updated_at")
