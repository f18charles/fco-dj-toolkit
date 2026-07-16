from django.db.models import QuerySet
from common.managers import BaseManager
from permissions.querysets import (
    PermissionQuerySet,
    RoleQuerySet,
    UserRoleQuerySet,
    UserPermissionQuerySet,
)


class PermissionManager(BaseManager):
    """
    Manager for Permission model.
    """

    def get_queryset(self) -> PermissionQuerySet:
        return PermissionQuerySet(self.model, using=self._db)

    def for_module(self, module: str) -> PermissionQuerySet:
        return self.get_queryset().for_module(module)

    def with_codename(self, codename: str) -> PermissionQuerySet:
        return self.get_queryset().with_codename(codename)


class RoleManager(BaseManager):
    """
    Manager for Role model.
    """

    def get_queryset(self) -> RoleQuerySet:
        return RoleQuerySet(self.model, using=self._db)

    def system_roles(self) -> RoleQuerySet:
        return self.get_queryset().system_roles()

    def user_roles(self) -> RoleQuerySet:
        return self.get_queryset().user_roles()

    def with_parent(self) -> RoleQuerySet:
        return self.get_queryset().with_parent()

    def root_roles(self) -> RoleQuerySet:
        return self.get_queryset().root_roles()


class UserRoleManager(BaseManager):
    """
    Manager for UserRole model.
    """

    def get_queryset(self) -> UserRoleQuerySet:
        return UserRoleQuerySet(self.model, using=self._db)

    def for_user(self, user) -> UserRoleQuerySet:
        return self.get_queryset().for_user(user)

    def active(self) -> UserRoleQuerySet:
        return self.get_queryset().active()

    def expired(self) -> UserRoleQuerySet:
        return self.get_queryset().expired()

    def for_role(self, role) -> UserRoleQuerySet:
        return self.get_queryset().for_role(role)


class UserPermissionManager(BaseManager):
    """
    Manager for UserPermission model.
    """

    def get_queryset(self) -> UserPermissionQuerySet:
        return UserPermissionQuerySet(self.model, using=self._db)

    def for_user(self, user) -> UserPermissionQuerySet:
        return self.get_queryset().for_user(user)

    def active(self) -> UserPermissionQuerySet:
        return self.get_queryset().active()

    def expired(self) -> UserPermissionQuerySet:
        return self.get_queryset().expired()
