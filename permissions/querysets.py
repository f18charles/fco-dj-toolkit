from django.utils import timezone

from common.querysets import BaseQuerySet


class PermissionQuerySet(BaseQuerySet):
    """
    QuerySet for Permission model.
    """
    def for_module(self, module: str) -> "PermissionQuerySet":
        return self.filter(module=module)

    def with_codename(self, codename: str) -> "PermissionQuerySet":
        return self.filter(codename=codename)


class RoleQuerySet(BaseQuerySet):
    """
    QuerySet for Role model.
    """
    def system_roles(self) -> "RoleQuerySet":
        return self.filter(is_system_role=True)

    def user_roles(self) -> "RoleQuerySet":
        return self.filter(is_system_role=False)

    def with_parent(self) -> "RoleQuerySet":
        return self.filter(parent__isnull=False)

    def root_roles(self) -> "RoleQuerySet":
        return self.filter(parent__isnull=True)


class UserRoleQuerySet(BaseQuerySet):
    """
    QuerySet for UserRole model.
    """
    def for_user(self, user) -> "UserRoleQuerySet":
        return self.filter(user=user)

    def active(self) -> "UserRoleQuerySet":
        now = timezone.now()
        return self.filter(expires_at__isnull=True) | self.filter(expires_at__gt=now)

    def expired(self) -> "UserRoleQuerySet":
        now = timezone.now()
        return self.filter(expires_at__isnull=False, expires_at__lte=now)

    def for_role(self, role) -> "UserRoleQuerySet":
        return self.filter(role=role)


class UserPermissionQuerySet(BaseQuerySet):
    """
    QuerySet for UserPermission model.
    """
    def for_user(self, user) -> "UserPermissionQuerySet":
        return self.filter(user=user)

    def active(self) -> "UserPermissionQuerySet":
        now = timezone.now()
        return self.filter(expires_at__isnull=True) | self.filter(expires_at__gt=now)

    def expired(self) -> "UserPermissionQuerySet":
        now = timezone.now()
        return self.filter(expires_at__isnull=False, expires_at__lte=now)
