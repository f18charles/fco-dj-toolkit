from io import BytesIO
from unittest.mock import patch, MagicMock
import json
import urllib.request
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware

from authentication.auth_methods.oauth2.providers import OAuth2ProviderConfig
from authentication.auth_methods.oauth2.models import SocialAccount
from authentication.auth_methods.oauth2 import services as oauth2_services
from authentication.tests.auth_methods.oauth2.factories import SocialAccountFactory
from users.tests.factories import UserFactory

User = get_user_model()


@pytest.fixture
def provider_config() -> OAuth2ProviderConfig:
    return OAuth2ProviderConfig(
        client_id="test-client-id",
        client_secret="test-client-secret",
        authorize_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/token",
        userinfo_url="https://example.com/oauth/userinfo",
        scopes=["read", "write"],
    )


def test_build_authorize_url(provider_config) -> None:
    url = oauth2_services.build_authorize_url(provider_config, "http://test/callback", "state123")
    assert "client_id=test-client-id" in url
    assert "redirect_uri=http%3B%2F%2Ftest%2Fcallback" in url or "redirect_uri=http%3A%2F%2Ftest%2Fcallback" in url
    assert "state=state123" in url
    assert "scope=read+write" in url or "scope=read%20write" in url


def test_exchange_code_success(provider_config) -> None:
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = json.dumps({"access_token": "token123"}).encode("utf-8")
    
    with patch.object(urllib.request, "urlopen", return_value=mock_response):
        token = oauth2_services.exchange_code(provider_config, "http://test/callback", "code123")
        assert token == "token123"


def test_fetch_profile_success(provider_config) -> None:
    profile_data = {"id": "12345", "email": "oauth@example.com", "name": "OAuth User"}
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = json.dumps(profile_data).encode("utf-8")

    with patch.object(urllib.request, "urlopen", return_value=mock_response):
        profile = oauth2_services.fetch_profile(provider_config, "token123")
        assert profile["email"] == "oauth@example.com"
        assert profile["id"] == "12345"


@pytest.mark.django_db
def test_get_or_create_user_existing_social_account() -> None:
    social_account = SocialAccountFactory(provider="google", provider_user_id="google-id-123")
    user = social_account.user

    # Resolves directly to the owner of the SocialAccount
    resolved_user = oauth2_services.get_or_create_user("google", {"sub": "google-id-123", "email": "test@example.com"})
    assert resolved_user == user


@pytest.mark.django_db
def test_get_or_create_user_email_match() -> None:
    user = UserFactory(email="match@example.com")
    
    # Matches existing user by email, and links it
    resolved_user = oauth2_services.get_or_create_user("github", {"id": "github-id-123", "email": "match@example.com"})
    assert resolved_user == user
    
    # Assert SocialAccount was created and linked
    assert SocialAccount.objects.filter(user=user, provider="github", provider_user_id="github-id-123").exists()


@pytest.mark.django_db
def test_get_or_create_user_new() -> None:
    # No matching social account or email exists -> Create new user
    resolved_user = oauth2_services.get_or_create_user("github", {"id": "new-github-id-999", "email": "new@example.com", "login": "newuser"})
    
    assert resolved_user.email == "new@example.com"
    assert resolved_user.username == "newuser"
    assert not resolved_user.has_usable_password()
    assert SocialAccount.objects.filter(user=resolved_user, provider="github", provider_user_id="new-github-id-999").exists()


@pytest.mark.django_db
def test_issue_final_credential_session(rf) -> None:
    user = UserFactory()
    user.backend = "authentication.core.backends.EmailOrUsernameBackend"
    request = rf.post("/login/")
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()

    payload = oauth2_services.issue_final_credential(user, request, issuer="session")
    assert payload["issuer"] == "session"
    assert "session_id" in payload
    assert "session_key" in payload


@pytest.mark.django_db
def test_issue_final_credential_token(rf) -> None:
    user = UserFactory()
    user.backend = "authentication.core.backends.EmailOrUsernameBackend"
    request = rf.post("/login/")

    payload = oauth2_services.issue_final_credential(user, request, issuer="token")
    assert payload["issuer"] == "token"
    assert "token" in payload


@pytest.mark.django_db
def test_issue_final_credential_jwt(rf) -> None:
    user = UserFactory()
    user.backend = "authentication.core.backends.EmailOrUsernameBackend"
    request = rf.post("/login/")

    payload = oauth2_services.issue_final_credential(user, request, issuer="jwt")
    assert payload["issuer"] == "jwt"
    assert "access" in payload
    assert "refresh" in payload
