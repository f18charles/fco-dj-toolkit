"""
Base manager for fco-dj-kit models.

``BaseManager`` pairs with ``BaseQuerySet`` so that models get the
timestamp-aware filters on ``objects`` by default.  Concrete model
managers should inherit from this (or from one of the specialised
managers below) and override ``get_queryset`` to return a more
specific queryset class when needed.
"""
from __future__ import annotations

import datetime

from django.db import models

from common.querysets.base import BaseQuerySet


class BaseManager(models.Manager):
    """
    Drop-in manager that returns a ``BaseQuerySet``.

    Proxy methods are provided on the manager itself so that the most
    common filters can be called directly::

        Post.objects.newest()
        Post.objects.created_in_last(days=7)

    Any filter not proxied here is still available via the queryset::

        Post.objects.all().created_since(some_dt).order_by("-title")
    """

    def get_queryset(self) -> BaseQuerySet:
        return BaseQuerySet(self.model, using=self._db)

    # ------------------------------------------------------------------
    # Proxied queryset methods for convenience
    # ------------------------------------------------------------------

    def created_since(self, dt: datetime.datetime) -> BaseQuerySet:
        """Proxy to :meth:`BaseQuerySet.created_since`."""
        return self.get_queryset().created_since(dt)

    def updated_since(self, dt: datetime.datetime) -> BaseQuerySet:
        """Proxy to :meth:`BaseQuerySet.updated_since`."""
        return self.get_queryset().updated_since(dt)

    def created_in_last(self, **timedelta_kwargs) -> BaseQuerySet:
        """Proxy to :meth:`BaseQuerySet.created_in_last`."""
        return self.get_queryset().created_in_last(**timedelta_kwargs)

    def updated_in_last(self, **timedelta_kwargs) -> BaseQuerySet:
        """Proxy to :meth:`BaseQuerySet.updated_in_last`."""
        return self.get_queryset().updated_in_last(**timedelta_kwargs)

    def newest(self) -> BaseQuerySet:
        """Proxy to :meth:`BaseQuerySet.newest`."""
        return self.get_queryset().newest()

    def oldest(self) -> BaseQuerySet:
        """Proxy to :meth:`BaseQuerySet.oldest`."""
        return self.get_queryset().oldest()

    def recently_updated(self) -> BaseQuerySet:
        """Proxy to :meth:`BaseQuerySet.recently_updated`."""
        return self.get_queryset().recently_updated()
