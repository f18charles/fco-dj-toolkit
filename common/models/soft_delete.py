from common.mixins.soft_delete_mixin import (
    SoftDeleteAllManager,
    SoftDeleteManager,
    SoftDeleteMixin,
)


class SoftDeleteModel(SoftDeleteMixin):
    """
    Abstract base model that implements soft deletion logic.
    Filters out soft-deleted items by default.
    """

    # Default manager only returns active items
    objects = SoftDeleteManager()

    # Manager to retrieve all items including deleted ones
    all_objects = SoftDeleteAllManager()

    class Meta:
        abstract = True
        base_manager_name = "all_objects"
