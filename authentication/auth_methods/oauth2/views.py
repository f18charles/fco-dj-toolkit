import secrets
from typing import Any
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View

from authentication.core.exceptions import AuthenticationModuleError
from authentication.auth_methods.oauth2 import services as oauth2_services


class OAuth2RedirectView(View):
    """
    Builds the authorize URL, saves the state token in the session for CSRF mitigation,
    and redirects the client to the OAuth2 provider.
    """

    def get(self, request, provider: str) -> Any:
        providers_config = getattr(settings, "OAUTH2_PROVIDERS", {})
        config = providers_config.get(provider.lower())
        if not config:
            return JsonResponse(
                {"error": f"Provider '{provider}' is not configured.", "code": "unconfigured_provider"},
                status=400,
            )

        # Generate and store a secure random token for CSRF verification
        state = secrets.token_urlsafe(32)
        request.session[f"oauth2_state_{provider.lower()}"] = state

        try:
            redirect_uri = request.build_absolute_uri(
                reverse("oauth2_auth:callback", kwargs={"provider": provider.lower()})
            )
        except Exception:
            # Fallback if reverse doesn't resolve in custom or test setups
            redirect_uri = request.build_absolute_uri(f"/auth/oauth2/{provider.lower()}/callback/")

        auth_url = oauth2_services.build_authorize_url(config, redirect_uri, state)
        return redirect(auth_url)


class OAuth2CallbackView(View):
    """
    Validates the state token, exchanges code for access token, fetches profile details,
    maps to a local User instance, and issues the final login credential.
    """

    def get(self, request, provider: str) -> JsonResponse:
        providers_config = getattr(settings, "OAUTH2_PROVIDERS", {})
        config = providers_config.get(provider.lower())
        if not config:
            return JsonResponse(
                {"error": f"Provider '{provider}' is not configured.", "code": "unconfigured_provider"},
                status=400,
            )

        # 1. State/CSRF validation
        state_in_url = request.GET.get("state")
        session_key = f"oauth2_state_{provider.lower()}"
        state_in_session = request.session.pop(session_key, None)

        if not state_in_session or state_in_url != state_in_session:
            return JsonResponse(
                {"error": "OAuth2 state validation failed (possible CSRF attack).", "code": "csrf_error"},
                status=400,
            )

        code = request.GET.get("code")
        if not code:
            return JsonResponse(
                {"error": "Authorization code not returned by provider.", "code": "missing_code"},
                status=400,
            )

        try:
            redirect_uri = request.build_absolute_uri(
                reverse("oauth2_auth:callback", kwargs={"provider": provider.lower()})
            )
        except Exception:
            redirect_uri = request.build_absolute_uri(f"/auth/oauth2/{provider.lower()}/callback/")

        try:
            # 2. Exchange authorization code
            access_token = oauth2_services.exchange_code(config, redirect_uri, code)

            # 3. Fetch remote profile
            profile = oauth2_services.fetch_profile(config, access_token)

            # 4. Resolve local user
            user = oauth2_services.get_or_create_user(provider.lower(), profile)

            # 5. Hand-off to issue final credential
            issuer_override = request.GET.get("issue")
            credential = oauth2_services.issue_final_credential(user, request, issuer=issuer_override)

            return JsonResponse(credential)
        except AuthenticationModuleError as e:
            return JsonResponse({"error": e.message, "code": e.code}, status=400)
