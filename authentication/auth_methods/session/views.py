import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from authentication.core.exceptions import AuthenticationModuleError, SessionNotFoundError
from authentication.core.services import AuthService
from authentication.auth_methods.session.services import SessionAuthMethod


class LoginView(View):
    """
    Form or JSON-based login view. Thinly wraps credential verification
    and session-issuing mechanisms.
    """

    @method_decorator(csrf_protect)
    def post(self, request) -> JsonResponse:
        identifier = request.POST.get("identifier")
        password = request.POST.get("password")

        if not identifier or not password:
            if request.content_type == "application/json":
                try:
                    data = json.loads(request.body)
                    identifier = data.get("identifier")
                    password = data.get("password")
                except json.JSONDecodeError:
                    pass

        if not identifier or not password:
            return JsonResponse(
                {"error": "Both identifier and password are required.", "code": "missing_fields"},
                status=400,
            )

        try:
            # 1. Verify credentials using core service
            user = AuthService.verify_credentials(
                identifier=identifier,
                password=password,
                request=request,
            )
            # 2. Complete session logging
            SessionAuthMethod.login(request, user)
            return JsonResponse({"message": "Successfully logged in.", "user_id": str(user.pk)})
        except AuthenticationModuleError as e:
            # Custom exceptions carry codes and messages
            return JsonResponse({"error": e.message, "code": e.code}, status=400)


class LogoutView(View):
    """
    Logout view that destroys the active session both in django storage and models.
    """

    @method_decorator(csrf_protect)
    def post(self, request) -> JsonResponse:
        SessionAuthMethod.logout(request)
        return JsonResponse({"message": "Successfully logged out."})


class SessionListView(View):
    """
    Lists all active sessions for the currently logged in user.
    """

    @method_decorator(login_required)
    def get(self, request) -> JsonResponse:
        sessions = SessionAuthMethod.list_active_sessions(request.user)
        session_list = [
            {
                "id": str(s.pk),
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "last_activity": s.last_activity.isoformat(),
                "is_current": s.session_key == request.session.session_key,
            }
            for s in sessions
        ]
        return JsonResponse({"sessions": session_list})


class SessionRevokeView(View):
    """
    Revokes a specific session belonging to the logged in user.
    """

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def post(self, request, session_id: str) -> JsonResponse:
        try:
            SessionAuthMethod.revoke_session(session_id, user=request.user)
            return JsonResponse({"message": "Session successfully revoked."})
        except SessionNotFoundError as e:
            return JsonResponse({"error": e.message, "code": e.code}, status=404)
