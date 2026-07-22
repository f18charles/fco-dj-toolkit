import factory

from common.factories import BaseFactory
from permissions.models import (
    Permission,
    Role,
    RolePermission,
    UserRole,
    UserPermission,
    ObjectPermission,
    ScopedUserRole,
    PermissionGroup,
)
from users.tests.factories import UserFactory


class PermissionFactory(BaseFactory):
    class Meta:
        model = Permission

    codename = factory.Sequence(lambda n: f"module{n}.action{n}")
    name = factory.Sequence(lambda n: f"Permission {n}")
    module = factory.LazyAttribute(lambda o: o.codename.split(".")[0])
    description = "Test permission"


class RoleFactory(BaseFactory):
    class Meta:
        model = Role

    name = factory.Sequence(lambda n: f"role_{n}")
    description = "Test role"
    parent = None
    is_system_role = False


class RolePermissionFactory(BaseFactory):
    class Meta:
        model = RolePermission

    role = factory.SubFactory(RoleFactory)
    permission = factory.SubFactory(PermissionFactory)
    granted_by = None


class UserRoleFactory(BaseFactory):
    class Meta:
        model = UserRole

    user = factory.SubFactory(UserFactory)
    role = factory.SubFactory(RoleFactory)
    granted_by = None
    expires_at = None


class UserPermissionFactory(BaseFactory):
    class Meta:
        model = UserPermission

    user = factory.SubFactory(UserFactory)
    permission = factory.SubFactory(PermissionFactory)
    granted_by = None
    expires_at = None


class ObjectPermissionFactory(BaseFactory):
    class Meta:
        model = ObjectPermission

    user = factory.SubFactory(UserFactory)
    permission = factory.SubFactory(PermissionFactory)
    content_object = factory.SubFactory(UserFactory)
    granted_by = None
    expires_at = None


class ScopedUserRoleFactory(BaseFactory):
    class Meta:
        model = ScopedUserRole

    user = factory.SubFactory(UserFactory)
    role = factory.SubFactory(RoleFactory)
    scope = factory.SubFactory(UserFactory)
    granted_by = None
    expires_at = None


class PermissionGroupFactory(BaseFactory):
    class Meta:
        model = PermissionGroup

    name = factory.Sequence(lambda n: f"group_{n}")
    description = "Test permission group"

