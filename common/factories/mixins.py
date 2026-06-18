"""
Factory Boy traits for common model behaviours.

These are ``factory.Trait`` declarations that can be mixed into any
concrete factory whose model uses one of the common abstract models.

Usage example::

    from common.factories import BaseFactory
    from common.factories.mixins import SoftDeletedTrait, InactiveTrait

    class ArticleFactory(BaseFactory):
        class Meta:
            model = Article

        title = factory.Sequence(lambda n: f"Article {n}")

        class Params:
            deleted = SoftDeletedTrait()
            inactive = InactiveTrait()

    # Build a soft-deleted article
    ArticleFactory(deleted=True)
"""
from __future__ import annotations

import factory
from django.utils import timezone


def SoftDeletedTrait() -> factory.Trait:
    """
    Returns a ``factory.Trait`` that marks an instance as soft-deleted.

    Declares:
        is_deleted = True
        deleted_at = <current time>
    """
    return factory.Trait(
        is_deleted=True,
        deleted_at=factory.LazyFunction(timezone.now),
    )


def InactiveTrait() -> factory.Trait:
    """
    Returns a ``factory.Trait`` that marks an instance as inactive.

    Requires the model to have an ``is_active`` field.
    """
    return factory.Trait(
        is_active=False,
    )


__all__ = [
    "InactiveTrait",
    "SoftDeletedTrait",
]
