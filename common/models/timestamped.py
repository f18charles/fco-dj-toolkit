from common.mixins.timestamp_mixin import TimestampMixin


class TimestampedModel(TimestampMixin):
    """
    Abstract base model that includes self-updating 'created_at' and 'updated_at' fields.
    """

    class Meta:
        abstract = True
