import pytest
from datetime import timedelta
from django.utils import timezone

from permissions.selectors import (
    get_all_permissions_for_user,
    get_roles_for_user,
    get_permissions_for_role,
    get_inherited_permissions_for_role,
    get_all_permissions_for_role,
    get_users_with_role,
    get_users_with_permission,
    get_active_role_assignments,
    get_expired_role_assignments,
    get_active_permission_grants,
)
from permissions.services import PermissionService, RoleService
from permissions.tests.factories import PermissionFactory, RoleFactory
from users.tests.factories import UserFactory
from permissions.models import UserRole

pytestmark = pytest.mark.django_db


class TestSelectors:
    def test_get_all_permissions_for_user(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        PermissionFactory(codename="posts.delete")
        PermissionFactory(codename="users.view")
        PermissionFactory(codename="users.create")
        
        # 1. Direct permission
        PermissionService.grant_permission_to_user(user=user, codename="users.view")
        
        # 2. Via role
        RoleService.create_role(name="editor")
        PermissionService.grant_permission_to_role(role_name="editor", codename="posts.edit")
        RoleService.assign_role(user=user, role_name="editor")
        
        # 3. Via parent role (inherited)
        RoleService.create_role(name="admin", parent_name="editor")
        PermissionService.grant_permission_to_role(role_name="admin", codename="posts.delete")
        
        # Another user assigned to admin to check isolation
        admin_user = UserFactory()
        RoleService.assign_role(user=admin_user, role_name="admin")
        
        # Check permissions for admin user (should inherit posts.edit from editor, plus posts.delete)
        admin_perms = get_all_permissions_for_user(admin_user)
        assert "posts.delete" in admin_perms
        assert "posts.edit" in admin_perms
        assert "users.view" not in admin_perms
        
        # Check permissions for first user (should have users.view, posts.edit)
        user_perms = get_all_permissions_for_user(user)
        assert "users.view" in user_perms
        assert "posts.edit" in user_perms
        assert "posts.delete" not in user_perms

    def test_get_roles_for_user_excludes_expired(self) -> None:
        user = UserFactory()
        RoleFactory(name="role_active")
        RoleFactory(name="role_expired")
        
        RoleService.assign_role(user=user, role_name="role_active")
        
        expired_time = timezone.now() - timedelta(seconds=1)
        RoleService.assign_role(user=user, role_name="role_expired", expires_at=expired_time)
        
        roles = get_roles_for_user(user)
        assert roles.count() == 1
        assert roles.filter(name="role_active").exists()
        assert not roles.filter(name="role_expired").exists()

    def test_get_all_permissions_for_role(self) -> None:
        PermissionFactory(codename="posts.edit")
        PermissionFactory(codename="posts.delete")
        
        editor = RoleService.create_role(name="editor")
        admin = RoleService.create_role(name="admin", parent_name="editor")
        
        PermissionService.grant_permission_to_role(role_name="editor", codename="posts.edit")
        PermissionService.grant_permission_to_role(role_name="admin", codename="posts.delete")
        
        assert get_permissions_for_role(editor).count() == 1
        assert get_inherited_permissions_for_role(editor).count() == 0
        
        assert get_permissions_for_role(admin).count() == 1
        assert get_inherited_permissions_for_role(admin).count() == 1
        
        admin_all_perms = get_all_permissions_for_role(admin)
        assert admin_all_perms == {"posts.edit", "posts.delete"}

    def test_get_users_with_role(self) -> None:
        u1 = UserFactory()
        u2 = UserFactory()
        RoleFactory(name="editor")
        
        RoleService.assign_role(user=u1, role_name="editor")
        
        expired_time = timezone.now() - timedelta(seconds=1)
        RoleService.assign_role(user=u2, role_name="editor", expires_at=expired_time)
        
        users = get_users_with_role("editor")
        assert users.count() == 1
        assert u1 in users
        assert u2 not in users

    def test_get_users_with_permission(self) -> None:
        u1 = UserFactory()
        u2 = UserFactory()
        u3 = UserFactory()
        
        PermissionFactory(codename="posts.edit")
        RoleFactory(name="editor")
        PermissionService.grant_permission_to_role(role_name="editor", codename="posts.edit")
        
        # 1. Direct permission
        PermissionService.grant_permission_to_user(user=u1, codename="posts.edit")
        # 2. Via role
        RoleService.assign_role(user=u2, role_name="editor")
        # 3. No permission
        
        users = get_users_with_permission("posts.edit")
        assert users.count() == 2
        assert u1 in users
        assert u2 in users
        assert u3 not in users

    def test_get_expired_role_assignments(self) -> None:
        u1 = UserFactory()
        RoleFactory(name="editor")
        RoleFactory(name="admin")
        
        RoleService.assign_role(user=u1, role_name="editor")
        
        expired_time = timezone.now() - timedelta(seconds=1)
        RoleService.assign_role(user=u1, role_name="admin", expires_at=expired_time)
        
        expired_assignments = get_expired_role_assignments()
        assert expired_assignments.count() == 1
        assert expired_assignments.first().role.name == "admin"
