"""
common.factories
================

Factory Boy base classes and traits for fco-dj-kit modules.

Every module in the kit should import ``BaseFactory`` from here rather
than from ``factory.django`` directly, and apply the shared traits from
``common.factories.mixins`` where appropriate.

    from common.factories import BaseFactory
    from common.factories.mixins import SoftDeletedTrait, InactiveTrait
"""
from common.factories.base import BaseFactory
from common.factories.mixins import InactiveTrait, SoftDeletedTrait

__all__ = [
    "BaseFactory",
    "InactiveTrait",
    "SoftDeletedTrait",
]
