from unittest.mock import patch
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned

from authentication.core.backends import EmailOrUsernameBackend
from users.tests.factories import UserFactory

User = get_user_model()


@pytest.mark.django_db
def test_authenticate_by_username_exact() -> None:
    backend = EmailOrUsernameBackend()
    user = UserFactory(username="exactusername", password="StrongPass123!")
    
    # Matching exactly
    authenticated = backend.authenticate(None, username="exactusername", password="StrongPass123!")
    assert authenticated == user

    # Wrong password
    assert backend.authenticate(None, username="exactusername", password="WrongPassword") is None


@pytest.mark.django_db
def test_authenticate_by_email_case_insensitive() -> None:
    backend = EmailOrUsernameBackend()
    user = UserFactory(username="user1", email="MyEmail@Example.Com", password="StrongPass123!")
    
    # Matching email case-insensitively
    authenticated = backend.authenticate(None, username="myemail@example.com", password="StrongPass123!")
    assert authenticated == user


@pytest.mark.django_db
def test_authenticate_no_match_hashing_timing_mitigation() -> None:
    backend = EmailOrUsernameBackend()
    
    # Mocking User.set_password to verify it is called when no match is found
    with patch.object(User, "set_password") as mock_set_password:
        result = backend.authenticate(None, username="nonexistent@example.com", password="somepassword")
        assert result is None
        mock_set_password.assert_called_once_with("somepassword")


@pytest.mark.django_db
def test_authenticate_multiple_objects_returned() -> None:
    backend = EmailOrUsernameBackend()
    
    # Create two users with different usernames but the same email (if allowed, or similar conflict)
    # Since email unique constraint is active on User, we can override or mock the query to raise MultipleObjectsReturned
    with patch.object(User.objects, "get", side_effect=MultipleObjectsReturned):
        result = backend.authenticate(None, username="duplicate@example.com", password="password")
        assert result is None
