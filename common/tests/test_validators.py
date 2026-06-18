from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from common.validators import (
    FileExtensionValidator,
    validate_phone_number,
    validate_slug,
    validate_username,
)


class DummyFile:
    def __init__(self, name):
        self.name = name


class ValidatorsTestCase(SimpleTestCase):
    """
    Test cases for custom validators in validators.py.
    """

    def test_validate_username(self):
        # Valid usernames
        valid = ["john_doe", "user.123", "abc-def", "123", "A_B.c-d"]
        for username in valid:
            try:
                validate_username(username)
            except ValidationError:
                self.fail(f"validate_username unexpectedly raised ValidationError for: {username}")

        # Invalid usernames
        invalid = [
            "jo",  # too short (len < 3)
            "a" * 31,  # too long (len > 30)
            "user name",  # contains space
            "user@123",  # invalid character @
            "user!",  # invalid character !
            "",  # empty
        ]
        for username in invalid:
            with self.assertRaises(ValidationError, msg=f"Failed to raise ValidationError for: {username}"):
                validate_username(username)

    def test_validate_slug(self):
        # Valid slugs
        valid = ["my-first-post", "post_123", "slug", "a-b-c"]
        for slug in valid:
            try:
                validate_slug(slug)
            except ValidationError:
                self.fail(f"validate_slug unexpectedly raised ValidationError for: {slug}")

        # Invalid slugs
        invalid = [
            "My-slug",  # uppercase
            "slug!",  # invalid char
            "slug with space",  # space
            "",  # empty
        ]
        for slug in invalid:
            with self.assertRaises(ValidationError, msg=f"Failed to raise ValidationError for: {slug}"):
                validate_slug(slug)

    def test_validate_phone_number(self):
        # Valid phone numbers (E.164-ish)
        valid = ["+1234567890", "999999999", "+999999999999999"]
        for phone in valid:
            try:
                validate_phone_number(phone)
            except ValidationError:
                self.fail(f"validate_phone_number unexpectedly raised ValidationError for: {phone}")

        # Invalid phone numbers
        invalid = [
            "+",  # only plus
            "1234567890123456",  # too long (16 digits, limit is 15)
            "123-456",  # hyphens
            "123a456",  # letters
            "",  # empty
        ]
        for phone in invalid:
            with self.assertRaises(ValidationError, msg=f"Failed to raise ValidationError for: {phone}"):
                validate_phone_number(phone)

    def test_file_extension_validator(self):
        validator = FileExtensionValidator(allowed_extensions=["png", ".jpg", "PDF"])

        # Valid files
        valid_files = [DummyFile("test.png"), DummyFile("image.jpg"), DummyFile("DOC.pdf")]
        for file in valid_files:
            try:
                validator(file)
            except ValidationError:
                self.fail(f"FileExtensionValidator unexpectedly raised ValidationError for file: {file.name}")

        # Invalid files
        invalid_files = [
            DummyFile("test.gif"),  # extension not allowed
            DummyFile("no_extension"),  # no extension at all
            DummyFile("image."),  # empty extension
        ]
        for file in invalid_files:
            with self.assertRaises(ValidationError, msg=f"Failed to raise ValidationError for file: {file.name}"):
                validator(file)
