"""
common.managers
===============

Re-usable Django Manager classes for fco-dj-kit models.

    from common.managers import BaseManager
    from common.managers import TimestampedSoftDeleteManager, TimestampedSoftDeleteAllManager
"""
from common.managers.base import BaseManager
from common.managers.soft_delete import (
    TimestampedSoftDeleteAllManager,
    TimestampedSoftDeleteManager,
)

__all__ = [
    "BaseManager",
    "TimestampedSoftDeleteAllManager",
    "TimestampedSoftDeleteManager",
]
