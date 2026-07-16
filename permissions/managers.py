from common.managers import BaseManager
from permissions.querysets import (
    PermissionQuerySet,
    RoleQuerySet,
    UserRoleQuerySet,
    UserPermissionQuerySet,
)


class PermissionManager(BaseManager.from_queryset(PermissionQuerySet)):
    """
    Manager for Permission model.
    """
    pass


class RoleManager(BaseManager.from_queryset(RoleQuerySet)):
    """
    Manager for Role model.
    """
    pass


class UserRoleManager(BaseManager.from_queryset(UserRoleQuerySet)):
    """
    Manager for UserRole model.
    """
    pass


class UserPermissionManager(BaseManager.from_queryset(UserPermissionQuerySet)):
    """
    Manager for UserPermission model.
    """
    pass
