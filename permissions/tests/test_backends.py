from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

from permissions.backends import RBACBackend
from permissions.services import PermissionService, RoleService
from permissions.tests.factories import PermissionFactory
from users.tests.factories import UserFactory


@override_settings(
    AUTHENTICATION_BACKENDS=[
        "django.contrib.auth.backends.ModelBackend",
        "permissions.backends.RBACBackend",
    ]
)
class TestRBACBackend(TestCase):
    def test_has_perm_assigned(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        RoleService.create_role(name="editor")
        PermissionService.grant_permission_to_role(role_name="editor", codename="posts.edit")
        RoleService.assign_role(user=user, role_name="editor")
        
        # Calls the auth backends under the hood
        assert user.has_perm("posts.edit") is True

    def test_has_perm_unassigned(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        
        assert user.has_perm("posts.edit") is False

    def test_has_module_perms_starts_with(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        RoleService.create_role(name="editor")
        PermissionService.grant_permission_to_role(role_name="editor", codename="posts.edit")
        RoleService.assign_role(user=user, role_name="editor")
        
        assert user.has_module_perms("posts") is True
        assert user.has_module_perms("other_app") is False

    def test_authenticate_returns_none(self) -> None:
        backend = RBACBackend()
        assert backend.authenticate(None, username="foo", password="bar") is None
