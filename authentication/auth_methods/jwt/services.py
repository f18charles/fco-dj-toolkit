from typing import Any, Dict

from django.apps import apps
from rest_framework_simplejwt.tokens import RefreshToken


def issue_pair(user: Any) -> Dict[str, str]:
    """
    Issue a new JWT access and refresh token pair for the user.
    """
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def revoke_refresh_token(token_str: str) -> None:
    """
    Revoke (blacklist) a refresh token.
    Requires 'rest_framework_simplejwt.token_blacklist' in INSTALLED_APPS.
    """
    if not apps.is_installed("rest_framework_simplejwt.token_blacklist"):
        raise NotImplementedError(
            "JWT revocation requires the token blacklist extension. "
            "Please add 'rest_framework_simplejwt.token_blacklist' to your INSTALLED_APPS."
        )

    # Blacklist the token by converting and calling blacklist method
    token = RefreshToken(token_str)
    token.blacklist()
