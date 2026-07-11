import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.auth_methods.jwt import services as jwt_services
from users.tests.factories import UserFactory


@pytest.mark.django_db
def test_jwt_issue_pair() -> None:
    user = UserFactory()
    tokens = jwt_services.issue_pair(user)
    
    assert "access" in tokens
    assert "refresh" in tokens
    
    # Verify signature and payload
    refresh = RefreshToken(tokens["refresh"])
    assert refresh["user_id"] == str(user.pk)


@pytest.mark.django_db
def test_jwt_revoke_token() -> None:
    user = UserFactory()
    tokens = jwt_services.issue_pair(user)
    refresh_token = tokens["refresh"]
    
    # Revoke (blacklist) the token
    jwt_services.revoke_refresh_token(refresh_token)
    
    # Token should be blacklisted (trying to load/validate should show it is in blacklist)
    # SimpleJWT's RefreshToken validation throws if blacklisted when we verify
    with pytest.raises(Exception):
        # This will trigger verification if blacklist check is active
        # (which it is since token_blacklist is in INSTALLED_APPS)
        token = RefreshToken(refresh_token)
        token.check_blacklist()
