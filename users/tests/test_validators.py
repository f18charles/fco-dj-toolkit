"""Tests for reusable validators."""
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from users.tests.factories import UserFactory
from users.validators import validate_avatar_image, validate_unique_email, validate_username

User = get_user_model()

pytestmark = pytest.mark.django_db


class FakeUploadedFile:
    """Minimal stand-in for Django's UploadedFile, for validator unit tests."""

    def __init__(self, content_type: str, size: int):
        self.content_type = content_type
        self.size = size


class TestValidateUsername:
    @pytest.mark.parametrize("username", ["abc", "valid.user-1", "a" * 30, "under_score"])
    def test_valid_usernames_do_not_raise(self, username):
        validate_username(username)

    @pytest.mark.parametrize(
        "username",
        ["ab", "a" * 31, "invalid user", "bad$char", "", None],
    )
    def test_invalid_usernames_raise(self, username):
        with pytest.raises(ValidationError):
            validate_username(username)


class TestValidateUniqueEmail:
    def test_raises_when_email_already_taken(self):
        UserFactory(email="taken@example.com")
        with pytest.raises(ValidationError):
            validate_unique_email("taken@example.com", User)

    def test_is_case_insensitive(self):
        UserFactory(email="taken@example.com")
        with pytest.raises(ValidationError):
            validate_unique_email("TAKEN@EXAMPLE.com", User)

    def test_passes_when_email_is_free(self):
        validate_unique_email("free@example.com", User)

    def test_passes_when_excluding_owners_own_pk(self):
        user = UserFactory(email="me@example.com")
        validate_unique_email("me@example.com", User, exclude_pk=user.pk)


class TestValidateAvatarImage:
    def test_valid_image_does_not_raise(self):
        validate_avatar_image(FakeUploadedFile("image/png", 1024))

    def test_invalid_content_type_raises(self):
        with pytest.raises(ValidationError):
            validate_avatar_image(FakeUploadedFile("application/pdf", 1024))

    def test_oversized_file_raises(self):
        with pytest.raises(ValidationError):
            validate_avatar_image(FakeUploadedFile("image/png", 10 * 1024 * 1024))

    def test_missing_metadata_does_not_raise(self):
        # Defensive: a file-like object without content_type/size attrs
        # should not crash the validator.
        class BareFile:
            pass

        validate_avatar_image(BareFile())
