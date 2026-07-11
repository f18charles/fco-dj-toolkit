import pytest
from rest_framework.authtoken.models import Token

from authentication.auth_methods.token import services as token_services
from users.tests.factories import UserFactory


@pytest.mark.django_db
def test_token_issue_rotate_revoke() -> None:
    user = UserFactory()
    
    # 1. Issue
    token = token_services.issue(user)
    assert token.user == user
    assert Token.objects.filter(user=user).count() == 1
    
    # 2. Re-issue (should retrieve same token)
    token2 = token_services.issue(user)
    assert token2 == token
    
    # 3. Rotate (should create new token and delete old)
    new_token = token_services.rotate(user)
    assert new_token != token
    assert Token.objects.filter(user=user).count() == 1
    
    # 4. Revoke (should delete token)
    token_services.revoke(user)
    assert Token.objects.filter(user=user).count() == 0
