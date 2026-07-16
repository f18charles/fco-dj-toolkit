import pytest
from permissions.registry import PermissionRegistry
from permissions.models import Permission

pytestmark = pytest.mark.django_db


class TestPermissionRegistry:
    def test_register_is_idempotent(self) -> None:
        registry = PermissionRegistry()
        registry.register(codename="posts.edit", name="Edit posts", module="posts", description="Desc")
        registry.register(codename="posts.edit", name="Edit posts", module="posts", description="Desc")
        
        registered = registry.get_registered()
        assert "posts.edit" in registered
        assert len(registered) == 1

    def test_sync_creates_rows_in_db_and_is_idempotent(self) -> None:
        registry = PermissionRegistry()
        registry.register(codename="posts.edit", name="Edit posts")
        registry.register(codename="posts.delete", name="Delete posts")

        # First sync
        created = registry.sync()
        assert len(created) == 2
        assert Permission.objects.filter(codename="posts.edit").exists()
        assert Permission.objects.filter(codename="posts.delete").exists()

        # Second sync should not create new rows
        created_again = registry.sync()
        assert len(created_again) == 0
        assert Permission.objects.count() == 2

    def test_is_registered(self) -> None:
        registry = PermissionRegistry()
        assert registry.is_registered("posts.edit") is False

        registry.register(codename="posts.edit", name="Edit posts")
        assert registry.is_registered("posts.edit") is True
