"""
Base Factory Boy factory for fco-dj-kit modules.

All factories across the kit should inherit from ``BaseFactory``
rather than ``DjangoModelFactory`` directly. This gives a single
place to set kit-wide factory configuration, override
``_create`` for multi-db support in the future, or add helpers
that every factory needs.
"""
from __future__ import annotations

import factory
from factory.django import DjangoModelFactory


class BaseFactory(DjangoModelFactory):
    """
    Kit-wide base factory.

    Conventions:
    - ``skip_postgeneration_save = True`` is set on all factories to
      avoid the double-save that factory_boy performs when
      post-generation hooks call ``.save()`` themselves.
    - Subclasses should override the inner ``Meta.model`` as usual.

    Example::

        class ArticleFactory(BaseFactory):
            class Meta:
                model = Article

            title = factory.Faker("sentence", nb_words=6)
            content = factory.Faker("paragraph")
    """

    class Meta:
        abstract = True
        skip_postgeneration_save = True
