from typing import Any
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class SoftDeleteQuerySet(models.QuerySet):
    """
    QuerySet that overrides standard deletion with soft-delete capabilities.
    """

    def delete(self) -> tuple[int, dict[str, int]]:
        """
        Soft delete all matching records in the QuerySet.
        """
        now = timezone.now()
        updated_count = self.update(is_deleted=True, deleted_at=now)
        # Returns standard Django delete format (total deleted, dict of counts per model)
        return updated_count, {self.model._meta.label: updated_count}

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        """
        Perform actual database deletion on matching records in the QuerySet.
        """
        return super().delete()

    def active(self) -> models.QuerySet:
        """
        Filter to only active (non-deleted) records.
        """
        return self.filter(is_deleted=False)

    def deleted(self) -> models.QuerySet:
        """
        Filter to only soft-deleted records.
        """
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """
    Manager that filters out soft-deleted records by default.
    """

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).active()


class SoftDeleteAllManager(models.Manager):
    """
    Manager that returns all records, including soft-deleted ones.
    """

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteMixin(models.Model):
    """
    Model mixin adding 'is_deleted' and 'deleted_at' fields with soft deletion support.
    """

    is_deleted = models.BooleanField(
        _("is deleted"),
        default=False,
        db_index=True,
    )
    deleted_at = models.DateTimeField(
        _("deleted at"),
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True

    def soft_delete(self) -> None:
        """
        Mark the record as deleted.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        """
        Override standard instance delete to perform a soft delete.
        """
        self.soft_delete()
        return 1, {self._meta.label: 1}

    def hard_delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        """
        Perform actual database deletion of the instance.
        """
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self) -> None:
        """
        Restore a soft-deleted record.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])
