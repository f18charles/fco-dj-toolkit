"""Tests for the custom UserManager / UserQuerySet."""
import pytest
from django.contrib.auth import get_user_model

from users.tests.factories import UserFactory

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestUserManagerCreation:
    def test_create_user_sets_usable_hashed_password(self):
        user = User.objects.create_user(
            username="janedoe", email="jane@example.com", password="secret123"
        )
        assert user.check_password("secret123")
        assert user.password != "secret123"
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_user_without_username_raises(self):
        with pytest.raises(ValueError):
            User.objects.create_user(username="", email="x@example.com", password="x")

    def test_create_user_without_email_raises(self):
        with pytest.raises(ValueError):
            User.objects.create_user(username="nomail", email="", password="x")

    def test_create_superuser_sets_staff_and_superuser_flags(self):
        user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="secret123"
        )
        assert user.is_staff
        assert user.is_superuser

    def test_create_superuser_rejects_is_staff_false(self):
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                username="admin2",
                email="admin2@example.com",
                password="x",
                is_staff=False,
            )

    def test_create_superuser_rejects_is_superuser_false(self):
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                username="admin3",
                email="admin3@example.com",
                password="x",
                is_superuser=False,
            )


class TestUserQuerySetFilters:
    def test_active_returns_only_active_users(self):
        UserFactory(username="active1", is_active=True)
        UserFactory(username="inactive1", is_active=False)
        assert User.objects.active().count() == 1

    def test_inactive_returns_only_inactive_users(self):
        UserFactory(username="active2", is_active=True)
        UserFactory(username="inactive2", is_active=False)
        assert User.objects.inactive().count() == 1

    def test_staff_returns_only_staff_users(self):
        UserFactory(username="staffuser", is_staff=True)
        UserFactory(username="regularuser", is_staff=False)
        assert User.objects.staff().count() == 1

    def test_filters_can_be_chained(self):
        UserFactory(username="activestaff", is_active=True, is_staff=True)
        UserFactory(username="inactivestaff", is_active=False, is_staff=True)
        UserFactory(username="activeuser", is_active=True, is_staff=False)

        assert User.objects.active().staff().count() == 1
