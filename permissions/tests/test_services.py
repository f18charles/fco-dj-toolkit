import pytest
from datetime import timedelta
from django.utils import timezone
from django.test import override_settings

from permissions.services import (
    PermissionService,
    RoleService,
    ObjectPermissionService,
    ScopedPermissionService,
)
from permissions.models import (
    Permission,
    Role,
    UserPermission,
    UserRole,
    RolePermission,
    ObjectPermission,
    ScopedUserRole,
)
from permissions.exceptions import (
    PermissionNotFoundError,
    PermissionAlreadyGrantedError,
    RoleNotFoundError,
    RoleAlreadyAssignedError,
    SystemRoleProtectedError,
    InvalidPermissionCodename,
    CircularRoleInheritanceError,
    ObjectPermissionNotFoundError,
    ObjectPermissionAlreadyGrantedError,
    ScopedRoleAlreadyAssignedError,
    ScopeRequiredError,
)
from permissions.tests.factories import PermissionFactory, RoleFactory
from users.tests.factories import UserFactory
from permissions.signals import role_assigned, role_revoked

pytestmark = pytest.mark.django_db


class TestPermissionService:
    def test_create_permission_valid_succeeds(self) -> None:
        perm = PermissionService.create_permission(
            codename="posts.edit", name="Can edit posts", module="posts", description="Edit posts desc"
        )
        assert perm.codename == "posts.edit"
        assert perm.name == "Can edit posts"
        assert perm.module == "posts"
        assert perm.description == "Edit posts desc"

    def test_create_permission_missing_dot_raises(self) -> None:
        with pytest.raises(InvalidPermissionCodename):
            PermissionService.create_permission(codename="editposts", name="Can edit posts")

    def test_create_permission_is_idempotent(self) -> None:
        perm1 = PermissionService.create_permission(codename="posts.edit", name="Edit 1")
        perm2 = PermissionService.create_permission(codename="posts.edit", name="Edit 2")
        assert perm1 == perm2
        assert Permission.objects.filter(codename="posts.edit").count() == 1

    def test_grant_permission_to_user_happy_path(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        up = PermissionService.grant_permission_to_user(user=user, codename="posts.edit")
        assert up.user == user
        assert up.permission.codename == "posts.edit"

    def test_grant_permission_to_user_duplicate_raises(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")
        with pytest.raises(PermissionAlreadyGrantedError):
            PermissionService.grant_permission_to_user(user=user, codename="posts.edit")

    def test_grant_permission_to_user_unknown_raises(self) -> None:
        user = UserFactory()
        with pytest.raises(PermissionNotFoundError):
            PermissionService.grant_permission_to_user(user=user, codename="unknown.perm")

    def test_revoke_permission_from_user_happy_path(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")
        
        # Verify it's there
        assert UserPermission.objects.filter(user=user, permission__codename="posts.edit").exists()
        
        PermissionService.revoke_permission_from_user(user=user, codename="posts.edit")
        assert not UserPermission.objects.filter(user=user, permission__codename="posts.edit").exists()

    def test_has_permission_direct_active(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")
        assert PermissionService.has_permission(user=user, codename="posts.edit") is True

    def test_has_permission_direct_expired(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        expired_time = timezone.now() - timedelta(seconds=1)
        PermissionService.grant_permission_to_user(
            user=user, codename="posts.edit", expires_at=expired_time
        )
        assert PermissionService.has_permission(user=user, codename="posts.edit") is False

    def test_has_permission_via_active_role(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        RoleService.create_role(name="editor")
        PermissionService.grant_permission_to_role(role_name="editor", codename="posts.edit")
        RoleService.assign_role(user=user, role_name="editor")
        assert PermissionService.has_permission(user=user, codename="posts.edit") is True

    def test_has_permission_via_parent_role(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        RoleService.create_role(name="editor")
        PermissionService.grant_permission_to_role(role_name="editor", codename="posts.edit")
        
        # admin role inherits from editor
        RoleService.create_role(name="admin", parent_name="editor")
        RoleService.assign_role(user=user, role_name="admin")
        
        assert PermissionService.has_permission(user=user, codename="posts.edit") is True

    def test_has_permission_via_expired_role(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        RoleService.create_role(name="editor")
        PermissionService.grant_permission_to_role(role_name="editor", codename="posts.edit")
        
        expired_time = timezone.now() - timedelta(seconds=1)
        RoleService.assign_role(user=user, role_name="editor", expires_at=expired_time)
        
        assert PermissionService.has_permission(user=user, codename="posts.edit") is False

    def test_has_permission_wildcard(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.*")
        PermissionFactory(codename="posts.edit")
        
        PermissionService.grant_permission_to_user(user=user, codename="posts.*")
        
        # user should have posts.edit (and posts.view, etc) via wildcard
        assert PermissionService.has_permission(user=user, codename="posts.edit") is True
        assert PermissionService.has_permission(user=user, codename="users.edit") is False

    @override_settings(PERMISSIONS_SUPERUSER_BYPASS=True)
    def test_has_permission_superuser_bypass_enabled(self) -> None:
        user = UserFactory(is_superuser=True)
        assert PermissionService.has_permission(user=user, codename="posts.edit") is True

    @override_settings(PERMISSIONS_SUPERUSER_BYPASS=False)
    def test_has_permission_superuser_bypass_disabled(self) -> None:
        user = UserFactory(is_superuser=True)
        # Without any permission grants, it should fall through to False
        assert PermissionService.has_permission(user=user, codename="posts.edit") is False

    def test_has_any_permission(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        PermissionFactory(codename="posts.delete")
        
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")
        
        assert PermissionService.has_any_permission(
            user=user, codenames=["posts.edit", "posts.delete"]
        ) is True
        assert PermissionService.has_any_permission(
            user=user, codenames=["posts.create", "posts.delete"]
        ) is False

    def test_has_all_permissions(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        PermissionFactory(codename="posts.delete")
        
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")
        
        assert PermissionService.has_all_permissions(
            user=user, codenames=["posts.edit"]
        ) is True
        assert PermissionService.has_all_permissions(
            user=user, codenames=["posts.edit", "posts.delete"]
        ) is False

    def test_grant_permission_to_role_happy_path(self) -> None:
        PermissionFactory(codename="posts.edit")
        RoleFactory(name="editor")
        rp = PermissionService.grant_permission_to_role(role_name="editor", codename="posts.edit")
        assert rp.role.name == "editor"
        assert rp.permission.codename == "posts.edit"

    def test_revoke_permission_from_role_happy_path(self) -> None:
        PermissionFactory(codename="posts.edit")
        RoleFactory(name="editor")
        PermissionService.grant_permission_to_role(role_name="editor", codename="posts.edit")
        
        assert RolePermission.objects.filter(role__name="editor", permission__codename="posts.edit").exists()
        
        PermissionService.revoke_permission_from_role(role_name="editor", codename="posts.edit")
        assert not RolePermission.objects.filter(role__name="editor", permission__codename="posts.edit").exists()


class TestRoleService:
    def test_create_role_happy_path(self) -> None:
        role = RoleService.create_role(name="editor", description="Editor role")
        assert role.name == "editor"
        assert role.description == "Editor role"
        assert role.parent is None

    def test_create_role_with_valid_parent(self) -> None:
        RoleService.create_role(name="editor")
        role = RoleService.create_role(name="admin", parent_name="editor")
        assert role.name == "admin"
        assert role.parent.name == "editor"

    def test_create_role_self_parent_raises(self) -> None:
        with pytest.raises(CircularRoleInheritanceError):
            RoleService.create_role(name="editor", parent_name="editor")

    def test_assign_role_happy_path_sends_signal(self) -> None:
        user = UserFactory()
        role = RoleFactory(name="editor")
        
        signals_received = []
        def handler(sender, user, role, granted_by, **kwargs):
            signals_received.append((user, role, granted_by))
        
        role_assigned.connect(handler)
        try:
            ur = RoleService.assign_role(user=user, role_name="editor")
            assert ur.user == user
            assert ur.role == role
            assert len(signals_received) == 1
            assert signals_received[0] == (user, role, None)
        finally:
            role_assigned.disconnect(handler)

    def test_assign_role_duplicate_raises(self) -> None:
        user = UserFactory()
        RoleFactory(name="editor")
        RoleService.assign_role(user=user, role_name="editor")
        with pytest.raises(RoleAlreadyAssignedError):
            RoleService.assign_role(user=user, role_name="editor")

    def test_revoke_role_happy_path_sends_signal(self) -> None:
        user = UserFactory()
        role = RoleFactory(name="editor")
        RoleService.assign_role(user=user, role_name="editor")
        
        signals_received = []
        def handler(sender, user, role, **kwargs):
            signals_received.append((user, role))
        
        role_revoked.connect(handler)
        try:
            RoleService.revoke_role(user=user, role_name="editor")
            assert not UserRole.objects.filter(user=user, role=role).exists()
            assert len(signals_received) == 1
            assert signals_received[0] == (user, role)
        finally:
            role_revoked.disconnect(handler)

    def test_clone_role_copies_permissions(self) -> None:
        PermissionFactory(codename="posts.edit")
        PermissionFactory(codename="posts.delete")
        RoleFactory(name="editor")
        PermissionService.grant_permission_to_role(role_name="editor", codename="posts.edit")
        PermissionService.grant_permission_to_role(role_name="editor", codename="posts.delete")
        
        cloned = RoleService.clone_role(source_role_name="editor", new_name="cloned_editor")
        assert cloned.name == "cloned_editor"
        assert cloned.parent is None
        
        cloned_perms = RolePermission.objects.filter(role=cloned).values_list(
            "permission__codename", flat=True
        )
        assert set(cloned_perms) == {"posts.edit", "posts.delete"}

    def test_delete_role_happy_path(self) -> None:
        RoleFactory(name="editor", is_system_role=False)
        RoleService.delete_role(role_name="editor")
        assert not Role.objects.filter(name="editor").exists()

    def test_delete_role_system_role_raises(self) -> None:
        RoleFactory(name="admin", is_system_role=True)
        with pytest.raises(SystemRoleProtectedError):
            RoleService.delete_role(role_name="admin")


class TestPermissionServiceV2Extensions:
    def test_has_permission_with_obj(self) -> None:
        user = UserFactory()
        target_obj = UserFactory()
        PermissionFactory(codename="posts.edit")

        assert PermissionService.has_permission(user=user, codename="posts.edit", obj=target_obj) is False

        ObjectPermissionService.grant(user=user, codename="posts.edit", obj=target_obj)
        assert PermissionService.has_permission(user=user, codename="posts.edit", obj=target_obj) is True

    def test_has_permission_with_obj_falls_through_to_global(self) -> None:
        user = UserFactory()
        target_obj = UserFactory()
        PermissionFactory(codename="posts.edit")
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")

        # User has global permission, so has_permission returns True even with obj
        assert PermissionService.has_permission(user=user, codename="posts.edit", obj=target_obj) is True

    def test_has_permission_with_scope(self) -> None:
        user = UserFactory()
        scope_obj = UserFactory()
        PermissionFactory(codename="posts.edit")
        RoleService.create_role(name="editor")
        PermissionService.grant_permission_to_role(role_name="editor", codename="posts.edit")

        # Global permission alone does not satisfy scoped check
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")
        assert PermissionService.has_permission(user=user, codename="posts.edit", scope=scope_obj) is False

        # Assigning scoped role satisfies scoped check
        ScopedPermissionService.assign_scoped_role(user=user, role_name="editor", scope=scope_obj)
        assert PermissionService.has_permission(user=user, codename="posts.edit", scope=scope_obj) is True


class TestObjectPermissionService:
    def test_grant_happy_path(self) -> None:
        user = UserFactory()
        target = UserFactory()
        PermissionFactory(codename="posts.edit")

        obj_perm = ObjectPermissionService.grant(user=user, codename="posts.edit", obj=target)
        assert obj_perm.user == user
        assert obj_perm.permission.codename == "posts.edit"
        assert obj_perm.content_object == target

    def test_grant_duplicate_raises(self) -> None:
        user = UserFactory()
        target = UserFactory()
        PermissionFactory(codename="posts.edit")
        ObjectPermissionService.grant(user=user, codename="posts.edit", obj=target)

        with pytest.raises(ObjectPermissionAlreadyGrantedError):
            ObjectPermissionService.grant(user=user, codename="posts.edit", obj=target)

    def test_grant_unknown_codename_raises(self) -> None:
        user = UserFactory()
        target = UserFactory()
        with pytest.raises(PermissionNotFoundError):
            ObjectPermissionService.grant(user=user, codename="unknown.perm", obj=target)

    def test_revoke_happy_path(self) -> None:
        user = UserFactory()
        target = UserFactory()
        PermissionFactory(codename="posts.edit")
        ObjectPermissionService.grant(user=user, codename="posts.edit", obj=target)

        ObjectPermissionService.revoke(user=user, codename="posts.edit", obj=target)
        assert ObjectPermissionService.has_object_permission(user=user, codename="posts.edit", obj=target) is False

    def test_revoke_not_found_raises(self) -> None:
        user = UserFactory()
        target = UserFactory()
        PermissionFactory(codename="posts.edit")
        with pytest.raises(ObjectPermissionNotFoundError):
            ObjectPermissionService.revoke(user=user, codename="posts.edit", obj=target)

    def test_has_object_permission_active_vs_expired(self) -> None:
        user = UserFactory()
        target = UserFactory()
        PermissionFactory(codename="posts.edit")

        past = timezone.now() - timedelta(days=1)
        ObjectPermissionService.grant(user=user, codename="posts.edit", obj=target, expires_at=past)

        assert ObjectPermissionService.has_object_permission(user=user, codename="posts.edit", obj=target) is False

    def test_get_objects_user_can_access(self) -> None:
        user = UserFactory()
        target1 = UserFactory()
        target2 = UserFactory()
        PermissionFactory(codename="posts.edit")

        ObjectPermissionService.grant(user=user, codename="posts.edit", obj=target1)
        qs = ObjectPermissionService.get_objects_user_can_access(user=user, codename="posts.edit", model_class=type(target1))
        assert list(qs) == [target1]


class TestScopedPermissionService:
    def test_assign_scoped_role_happy_path(self) -> None:
        user = UserFactory()
        scope = UserFactory()
        RoleService.create_role(name="editor")

        sr = ScopedPermissionService.assign_scoped_role(user=user, role_name="editor", scope=scope)
        assert sr.user == user
        assert sr.role.name == "editor"
        assert sr.scope == scope

    def test_assign_scoped_role_duplicate_raises(self) -> None:
        user = UserFactory()
        scope = UserFactory()
        RoleService.create_role(name="editor")

        ScopedPermissionService.assign_scoped_role(user=user, role_name="editor", scope=scope)
        with pytest.raises(ScopedRoleAlreadyAssignedError):
            ScopedPermissionService.assign_scoped_role(user=user, role_name="editor", scope=scope)

    def test_revoke_scoped_role_happy_path(self) -> None:
        user = UserFactory()
        scope = UserFactory()
        RoleService.create_role(name="editor")
        ScopedPermissionService.assign_scoped_role(user=user, role_name="editor", scope=scope)

        ScopedPermissionService.revoke_scoped_role(user=user, role_name="editor", scope=scope)
        roles = ScopedPermissionService.get_scoped_roles_for_user(user=user, scope=scope)
        assert roles.count() == 0

    def test_get_all_permissions_for_user_in_scope_includes_parent_role(self) -> None:
        user = UserFactory()
        scope = UserFactory()
        PermissionFactory(codename="posts.edit")

        RoleService.create_role(name="editor")
        PermissionService.grant_permission_to_role(role_name="editor", codename="posts.edit")

        RoleService.create_role(name="admin", parent_name="editor")
        ScopedPermissionService.assign_scoped_role(user=user, role_name="admin", scope=scope)

        perms = ScopedPermissionService.get_all_permissions_for_user_in_scope(user=user, scope=scope)
        assert "posts.edit" in perms

