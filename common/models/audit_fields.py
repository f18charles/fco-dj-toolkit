from common.mixins.user_tracking_mixin import UserTrackingMixin


class AuditFieldsModel(UserTrackingMixin):
    """
    Abstract base model that includes user tracking fields: created_by and updated_by.
    """

    class Meta:
        abstract = True
