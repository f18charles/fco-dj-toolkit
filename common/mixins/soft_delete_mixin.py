from typing import Any

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class SoftDeleteQuerySet(models.QuerySet):
    """
    QuerySet that overrides standard deletion with soft-delete capabilities.
    """

    def delete(self) -> tuple[int, dict[str, int]]:
        """Soft delete all matching records in the QuerySet."""
        now = timezone.now()
        update_kwargs: dict[str, Any] = {"is_deleted": True, "deleted_at": now}

        # Honour updated_at if the model has the timestamp mixin.
        if hasattr(self.model, "updated_at"):
            update_kwargs["updated_at"] = now

        updated_count = self.update(**update_kwargs)
        return updated_count, {self.model._meta.label: updated_count}

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        """Perform actual database deletion on matching records."""
        return super().delete()

    def active(self) -> "SoftDeleteQuerySet":
        """Filter to only active (non-deleted) records."""
        return self.filter(is_deleted=False)

    def deleted(self) -> "SoftDeleteQuerySet":
        """Filter to only soft-deleted records."""
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Manager that filters out soft-deleted records by default."""

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).active()


class SoftDeleteAllManager(models.Manager):
    """Manager that returns all records, including soft-deleted ones."""

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteMixin(models.Model):
    """
    Model mixin adding ``is_deleted`` and ``deleted_at`` fields with
    soft deletion support.

    Instance-level ``delete()`` / ``restore()`` also write ``updated_at``
    when the model inherits ``TimestampMixin``, keeping the audit trail
    consistent.
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
        """Mark the record as deleted."""
        now = timezone.now()
        self.is_deleted = True
        self.deleted_at = now

        update_fields = ["is_deleted", "deleted_at"]
        if hasattr(self, "updated_at"):
            self.updated_at = now  # type: ignore[attr-defined]
            update_fields.append("updated_at")

        self.save(update_fields=update_fields)

    def delete(
        self, using: Any = None, keep_parents: bool = False
    ) -> tuple[int, dict[str, int]]:
        """Override instance delete to perform a soft delete."""
        self.soft_delete()
        return 1, {self._meta.label: 1}

    def hard_delete(
        self, using: Any = None, keep_parents: bool = False
    ) -> tuple[int, dict[str, int]]:
        """Perform actual database deletion of this instance."""
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        now = timezone.now()
        self.is_deleted = False
        self.deleted_at = None

        update_fields = ["is_deleted", "deleted_at"]
        if hasattr(self, "updated_at"):
            self.updated_at = now  # type: ignore[attr-defined]
            update_fields.append("updated_at")

        self.save(update_fields=update_fields)
