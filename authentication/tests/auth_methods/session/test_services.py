from typing import Any
import pytest
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from authentication.core.exceptions import SessionNotFoundError
from authentication.auth_methods.session.services import SessionAuthMethod
from authentication.auth_methods.session.models import UserSession
from authentication.tests.auth_methods.session.factories import UserSessionFactory
from users.tests.factories import UserFactory

User = get_user_model()


@pytest.fixture
def http_request() -> Any:
    # Build a request with session support
    rf = RequestFactory()
    request = rf.post("/login/")
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()
    return request


@pytest.mark.django_db
def test_session_login_logout(http_request) -> None:
    user = UserFactory(password="StrongPass123!")
    
    # 1. Login
    user_session = SessionAuthMethod.login(http_request, user)
    assert user_session.user == user
    assert user_session.is_active is True
    assert user_session.session_key == http_request.session.session_key
    
    # 2. Logout
    SessionAuthMethod.logout(http_request)
    user_session.refresh_from_db()
    assert user_session.is_active is False


@pytest.mark.django_db
def test_session_management() -> None:
    user = UserFactory()
    
    # Create active sessions
    session1 = UserSessionFactory(user=user)
    session2 = UserSessionFactory(user=user)
    
    # List active sessions
    active_sessions = SessionAuthMethod.list_active_sessions(user)
    assert active_sessions.count() == 2
    
    # Revoke specific session
    SessionAuthMethod.revoke_session(str(session1.pk), user=user)
    session1.refresh_from_db()
    assert session1.is_active is False
    assert SessionAuthMethod.list_active_sessions(user).count() == 1


@pytest.mark.django_db
def test_revoke_session_not_found() -> None:
    user1 = UserFactory()
    user2 = UserFactory()
    
    session_of_user1 = UserSessionFactory(user=user1)

    # Trying to revoke user1's session using user2 context should fail
    with pytest.raises(SessionNotFoundError):
        SessionAuthMethod.revoke_session(str(session_of_user1.pk), user=user2)


@pytest.mark.django_db
def test_revoke_all_other_sessions() -> None:
    user = UserFactory()
    
    session1 = UserSessionFactory(user=user)
    session2 = UserSessionFactory(user=user)
    session3 = UserSessionFactory(user=user)
    
    # Revoke all except session3
    SessionAuthMethod.revoke_all_other_sessions(user, current_session_key=session3.session_key)
    
    session1.refresh_from_db()
    session2.refresh_from_db()
    session3.refresh_from_db()
    
    assert session1.is_active is False
    assert session2.is_active is False
    assert session3.is_active is True
