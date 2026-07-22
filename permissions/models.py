from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import UUIDModel, TimestampedModel
from permissions.managers import (
    PermissionManager,
    RoleManager,
    UserRoleManager,
    UserPermissionManager,
    ObjectPermissionManager,
    ScopedUserRoleManager,
    PermissionGroupManager,
)



def validate_codename_has_one_dot(value: str) -> None:
    """Validate that the permission codename contains exactly one dot."""
    if not isinstance(value, str) or value.count(".") != 1:
        raise ValidationError(
            _("Permission codename must contain exactly one dot (e.g., 'module.action').")
        )


class Permission(UUIDModel, TimestampedModel):
    """
    Stores individual permission codenames defined by application modules.
    """
    codename = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        validators=[validate_codename_has_one_dot],
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=64, blank=True)

    objects = PermissionManager()

    class Meta:
        verbose_name = _("permission")
        verbose_name_plural = _("permissions")
        ordering = ["module", "codename"]

    def __str__(self) -> str:
        return self.codename

    def clean(self) -> None:
        super().clean()
        validate_codename_has_one_dot(self.codename)


class Role(UUIDModel, TimestampedModel):
    """
    Groups permissions together to assign access levels to users.
    """
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    is_system_role = models.BooleanField(default=False)

    objects = RoleManager()

    class Meta:
        verbose_name = _("role")
        verbose_name_plural = _("roles")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class RolePermission(UUIDModel, TimestampedModel):
    """
    Explicit through table for Role and Permission M2M relationship.
    """
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _("role permission")
        verbose_name_plural = _("role permissions")
        unique_together = [("role", "permission")]

    def __str__(self) -> str:
        return f"{self.role.name} -> {self.permission.codename}"


class UserRole(UUIDModel, TimestampedModel):
    """
    Links a User to a Role, with optional expiration support.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="granted_user_roles",
    )
    expires_at = models.DateTimeField(null=True, blank=True)

    objects = UserRoleManager()

    class Meta:
        verbose_name = _("user role")
        verbose_name_plural = _("user roles")
        unique_together = [("user", "role")]

    def __str__(self) -> str:
        return f"{self.user} has role {self.role.name}"


class UserPermission(UUIDModel, TimestampedModel):
    """
    Allows direct direct permission assignment to a user, bypassing roles.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_permissions_direct",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="user_permissions",
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="granted_user_permissions",
    )
    expires_at = models.DateTimeField(null=True, blank=True)

    objects = UserPermissionManager()

    class Meta:
        verbose_name = _("user permission")
        verbose_name_plural = _("user permissions")
        unique_together = [("user", "permission")]

    def __str__(self) -> str:
        return f"{self.user} has permission {self.permission.codename}"


class ObjectPermission(UUIDModel, TimestampedModel):
    """
    Grants a specific permission to a specific user on a specific model instance via GFK.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="object_permissions",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="object_permissions",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey("content_type", "object_id")
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="granted_object_permissions",
    )
    expires_at = models.DateTimeField(null=True, blank=True)

    objects = ObjectPermissionManager()

    class Meta:
        verbose_name = _("object permission")
        verbose_name_plural = _("object permissions")
        unique_together = [("user", "permission", "content_type", "object_id")]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["user", "content_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} has {self.permission.codename} on {self.content_type.model}:{self.object_id}"


class ScopedUserRole(UUIDModel, TimestampedModel):
    """
    A role assignment scoped to a specific object (e.g. an organization, project).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scoped_user_roles",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="scoped_user_roles",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    scope = GenericForeignKey("content_type", "object_id")
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="granted_scoped_user_roles",
    )
    expires_at = models.DateTimeField(null=True, blank=True)

    objects = ScopedUserRoleManager()

    class Meta:
        verbose_name = _("scoped user role")
        verbose_name_plural = _("scoped user roles")
        unique_together = [("user", "role", "content_type", "object_id")]

    def __str__(self) -> str:
        return f"{self.user} has role {self.role.name} on {self.content_type.model}:{self.object_id}"


class PermissionGroup(UUIDModel, TimestampedModel):
    """
    A named grouping of permissions for display/organisational purposes in admin UI.
    """
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="permission_groups",
    )

    objects = PermissionGroupManager()

    class Meta:
        verbose_name = _("permission group")
        verbose_name_plural = _("permission groups")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
