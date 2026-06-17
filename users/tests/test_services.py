"""Tests for the UserService business-logic layer."""
import uuid

import pytest

from users.exceptions import (
    EmailAlreadyExistsError,
    UserAlreadyActiveError,
    UserAlreadyInactiveError,
    UserNotFoundError,
)
from users.services import UserService
from users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestCreateUser:
    def test_creates_user_with_hashed_password(self):
        user = UserService.create_user(
            username="newuser", email="new@example.com", password="secret123"
        )
        assert user.pk is not None
        assert user.check_password("secret123")

    def test_raises_when_email_already_taken(self):
        UserFactory(email="taken@example.com")
        with pytest.raises(EmailAlreadyExistsError):
            UserService.create_user(
                username="another", email="taken@example.com", password="secret123"
            )

    def test_passes_through_extra_fields(self):
        user = UserService.create_user(
            username="extrafields",
            email="extra@example.com",
            password="secret123",
            first_name="Extra",
        )
        assert user.first_name == "Extra"


class TestDeactivateAndActivateUser:
    def test_deactivate_user_sets_is_active_false(self):
        user = UserFactory(is_active=True)
        result = UserService.deactivate_user(user_id=user.pk)
        assert result.is_active is False

    def test_deactivate_already_inactive_user_raises(self):
        user = UserFactory(is_active=False)
        with pytest.raises(UserAlreadyInactiveError):
            UserService.deactivate_user(user_id=user.pk)

    def test_deactivate_nonexistent_user_raises_not_found(self):
        with pytest.raises(UserNotFoundError):
            UserService.deactivate_user(user_id=uuid.uuid4())

    def test_activate_user_sets_is_active_true(self):
        user = UserFactory(is_active=False)
        result = UserService.activate_user(user_id=user.pk)
        assert result.is_active is True

    def test_activate_already_active_user_raises(self):
        user = UserFactory(is_active=True)
        with pytest.raises(UserAlreadyActiveError):
            UserService.activate_user(user_id=user.pk)

    def test_activate_nonexistent_user_raises_not_found(self):
        with pytest.raises(UserNotFoundError):
            UserService.activate_user(user_id=uuid.uuid4())


class TestUpdateProfile:
    def test_updates_allowed_fields(self):
        user = UserFactory(first_name="Old")
        result = UserService.update_profile(user_id=user.pk, first_name="New")
        assert result.first_name == "New"

    def test_ignores_protected_fields_like_email(self):
        user = UserFactory(email="protected@example.com")
        UserService.update_profile(user_id=user.pk, email="hacked@example.com")
        user.refresh_from_db()
        assert user.email == "protected@example.com"

    def test_ignores_protected_fields_like_is_staff(self):
        user = UserFactory(is_staff=False)
        UserService.update_profile(user_id=user.pk, is_staff=True)
        user.refresh_from_db()
        assert user.is_staff is False

    def test_no_fields_is_a_no_op(self):
        user = UserFactory(first_name="Stays")
        result = UserService.update_profile(user_id=user.pk)
        assert result.first_name == "Stays"


class TestChangeEmail:
    def test_changes_email_successfully(self):
        user = UserFactory(email="old@example.com")
        result = UserService.change_email(user_id=user.pk, new_email="new@example.com")
        assert result.email == "new@example.com"

    def test_raises_when_new_email_already_taken_by_another_user(self):
        UserFactory(email="taken@example.com")
        user = UserFactory(email="mine@example.com")
        with pytest.raises(EmailAlreadyExistsError):
            UserService.change_email(user_id=user.pk, new_email="taken@example.com")

    def test_allows_setting_same_email_user_already_has(self):
        user = UserFactory(email="same@example.com")
        result = UserService.change_email(user_id=user.pk, new_email="same@example.com")
        assert result.email == "same@example.com"
