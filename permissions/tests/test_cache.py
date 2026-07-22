import pytest
from django.conf import settings
from permissions.cache import (
    get_user_permissions_from_cache,
    set_user_permissions_cache,
    invalidate_user_permissions_cache,
)
from permissions.services import PermissionService, RoleService
from permissions.tests.factories import (
    UserFactory,
    PermissionFactory,
    RoleFactory,
    UserPermissionFactory,
    UserRoleFactory,
)


@pytest.mark.django_db
class TestPermissionsCache:
    def test_cache_round_trip(self) -> None:
        user = UserFactory()
        perms = {"posts.view", "posts.edit"}
        set_user_permissions_cache(user, perms)

        cached = get_user_permissions_from_cache(user)
        assert cached == perms

    def test_cache_returns_none_for_uncached(self) -> None:
        user = UserFactory()
        assert get_user_permissions_from_cache(user) is None

    def test_invalidate_user_permissions_cache(self) -> None:
        user = UserFactory()
        set_user_permissions_cache(user, {"posts.view"})
        assert get_user_permissions_from_cache(user) == {"posts.view"}

        invalidate_user_permissions_cache(user)
        assert get_user_permissions_from_cache(user) is None

    def test_saving_user_role_triggers_invalidation(self) -> None:
        user = UserFactory()
        role = RoleFactory()
        set_user_permissions_cache(user, {"posts.view"})
        user._permissions_cache = {"posts.view"}

        UserRoleFactory(user=user, role=role)

        assert get_user_permissions_from_cache(user) is None
        assert not hasattr(user, "_permissions_cache")

    def test_saving_user_permission_triggers_invalidation(self) -> None:
        user = UserFactory()
        perm = PermissionFactory(codename="posts.edit")
        set_user_permissions_cache(user, {"posts.view"})
        user._permissions_cache = {"posts.view"}

        UserPermissionFactory(user=user, permission=perm)

        assert get_user_permissions_from_cache(user) is None
        assert not hasattr(user, "_permissions_cache")

    def test_has_permission_populates_and_uses_cache(self, django_assert_num_queries) -> None:
        user = UserFactory()
        perm = PermissionFactory(codename="posts.edit")
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")

        # Invalidate in-memory cache on user
        if hasattr(user, "_permissions_cache"):
            del user._permissions_cache

        # First call populates cache
        assert PermissionService.has_permission(user=user, codename="posts.edit") is True

        # Delete in-memory cache to force reading from cache backend
        del user._permissions_cache

        # Second call should use cache without hitting DB for user permissions resolution
        with django_assert_num_queries(0):
            assert PermissionService.has_permission(user=user, codename="posts.edit") is True

    def test_cache_fallback_when_backend_not_set(self, settings) -> None:
        settings.PERMISSIONS_CACHE_BACKEND = None
        user = UserFactory()

        set_user_permissions_cache(user, {"posts.view"})
        assert get_user_permissions_from_cache(user) is None
