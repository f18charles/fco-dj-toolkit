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


class ObjectPermissionQuerySet(BaseQuerySet):
    """
    QuerySet for ObjectPermission model.
    """
    def for_user(self, user) -> "ObjectPermissionQuerySet":
        return self.filter(user=user)

    def for_object(self, obj) -> "ObjectPermissionQuerySet":
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(obj)
        return self.filter(content_type=ct, object_id=str(obj.pk))

    def for_permission(self, codename: str) -> "ObjectPermissionQuerySet":
        return self.filter(permission__codename=codename)

    def active(self) -> "ObjectPermissionQuerySet":
        now = timezone.now()
        return self.filter(expires_at__isnull=True) | self.filter(expires_at__gt=now)

    def expired(self) -> "ObjectPermissionQuerySet":
        now = timezone.now()
        return self.filter(expires_at__isnull=False, expires_at__lte=now)


class ScopedUserRoleQuerySet(BaseQuerySet):
    """
    QuerySet for ScopedUserRole model.
    """
    def for_user(self, user) -> "ScopedUserRoleQuerySet":
        return self.filter(user=user)

    def for_scope(self, scope_obj) -> "ScopedUserRoleQuerySet":
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(scope_obj)
        return self.filter(content_type=ct, object_id=str(scope_obj.pk))

    def for_role(self, role) -> "ScopedUserRoleQuerySet":
        if isinstance(role, str):
            return self.filter(role__name=role)
        return self.filter(role=role)

    def active(self) -> "ScopedUserRoleQuerySet":
        now = timezone.now()
        return self.filter(expires_at__isnull=True) | self.filter(expires_at__gt=now)

    def expired(self) -> "ScopedUserRoleQuerySet":
        now = timezone.now()
        return self.filter(expires_at__isnull=False, expires_at__lte=now)


class PermissionGroupQuerySet(BaseQuerySet):
    """
    QuerySet for PermissionGroup model.
    """
    def containing_permission(self, codename: str) -> "PermissionGroupQuerySet":
        return self.filter(permissions__codename=codename)

