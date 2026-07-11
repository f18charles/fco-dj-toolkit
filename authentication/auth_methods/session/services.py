from __future__ import annotations

from typing import Any, Optional

from django.contrib.auth import login as django_login, logout as django_logout
from django.db.models import QuerySet
from django.http import HttpRequest

from authentication.core.exceptions import SessionNotFoundError
from authentication.auth_methods.session.models import UserSession


class SessionAuthMethod:
    """
    Implements session-based login and logout procedures, and manages user session records.
    """

    @staticmethod
    def login(request: HttpRequest, user: Any) -> UserSession:
        """
        Log the user in using Django's session engine and create/update a UserSession.
        """
        # Call Django's login to cycle the session key and bind the user
        django_login(request, user)

        session_key = request.session.session_key
        if not session_key:
            # Force session key creation if it wasn't generated automatically
            request.session.save()
            session_key = request.session.session_key

        ip_address = None
        user_agent = ""

        if request is not None:
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(",")[0].strip()
            else:
                ip_address = request.META.get("REMOTE_ADDR")

        user_session, _ = UserSession.objects.update_or_create(
            session_key=session_key,
            defaults={
                "user": user,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "is_active": True,
            },
        )
        return user_session

    @staticmethod
    def logout(request: HttpRequest) -> None:
        """
        Log the user out and mark the current active session record as inactive.
        """
        session_key = getattr(request.session, "session_key", None)
        if session_key:
            UserSession.objects.filter(session_key=session_key).update(is_active=False)

        django_logout(request)

    @staticmethod
    def list_active_sessions(user: Any) -> QuerySet[UserSession]:
        """
        List all active sessions for a given user.
        """
        return UserSession.objects.for_user(user).active()

    @staticmethod
    def revoke_session(session_id: str, *, user: Any) -> None:
        """
        Revoke a specific session.
        Raises SessionNotFoundError if the session is not found or does not belong to the user.
        """
        try:
            session = UserSession.objects.get(pk=session_id, user=user)
        except (UserSession.DoesNotExist, ValueError, TypeError):
            raise SessionNotFoundError("Session not found or already revoked.")

        session.revoke()

    @staticmethod
    def revoke_all_other_sessions(user: Any, *, current_session_key: str) -> None:
        """
        Revoke all other active sessions for the user except the current one.
        """
        other_sessions = UserSession.objects.for_user(user).active().exclude(session_key=current_session_key)
        for session in other_sessions:
            session.revoke()
