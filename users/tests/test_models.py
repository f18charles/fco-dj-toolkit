"""Tests for the User model."""
import uuid

import pytest

from users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestUserModel:
    def test_user_has_uuid_primary_key(self):
        user = UserFactory()
        assert isinstance(user.pk, uuid.UUID)

    def test_email_must_be_unique(self):
        UserFactory(email="dup@example.com")
        with pytest.raises(Exception):
            UserFactory(username="other", email="dup@example.com")

    def test_created_at_and_updated_at_are_populated(self):
        user = UserFactory()
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_updated_at_changes_on_save(self):
        user = UserFactory()
        original_updated_at = user.updated_at
        user.first_name = "Changed"
        user.save()
        user.refresh_from_db()
        assert user.updated_at >= original_updated_at

    def test_str_representation_returns_email(self):
        user = UserFactory(email="someone@example.com")
        assert str(user) == "someone@example.com"

    def test_full_name_property_uses_first_and_last_name(self):
        user = UserFactory(first_name="Ada", last_name="Lovelace")
        assert user.full_name == "Ada Lovelace"

    def test_full_name_property_falls_back_to_username(self):
        user = UserFactory(username="nonameuser", first_name="", last_name="")
        assert user.full_name == "nonameuser"
