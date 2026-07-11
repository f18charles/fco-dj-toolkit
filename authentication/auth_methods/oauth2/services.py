from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from authentication.core.exceptions import AuthenticationModuleError
from authentication.auth_methods.oauth2.providers import OAuth2ProviderConfig


def build_authorize_url(provider_config: OAuth2ProviderConfig, redirect_uri: str, state: str) -> str:
    """
    Build the authorization redirect URL for OAuth2.
    """
    params = {
        "client_id": provider_config.client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(provider_config.scopes),
        "state": state,
    }
    return f"{provider_config.authorize_url}?{urllib.parse.urlencode(params)}"


def exchange_code(provider_config: OAuth2ProviderConfig, redirect_uri: str, code: str) -> str:
    """
    Exchange authorization code for an access token.
    Uses standard urllib.request to avoid external third-party dependencies.
    """
    payload = {
        "client_id": provider_config.client_id,
        "client_secret": provider_config.client_secret,
        "redirect_uri": redirect_uri,
        "code": code,
        "grant_type": "authorization_code",
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    req = urllib.request.Request(
        provider_config.token_url,
        data=data,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            if "access_token" in res_body:
                return res_body["access_token"]
            raise AuthenticationModuleError("Access token not found in provider response.")
    except Exception as e:
        raise AuthenticationModuleError(f"OAuth2 code exchange failed: {str(e)}")


def fetch_profile(provider_config: OAuth2ProviderConfig, access_token: str) -> dict:
    """
    Fetch user profile details from userinfo endpoint.
    Uses standard urllib.request.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    req = urllib.request.Request(
        provider_config.userinfo_url,
        headers=headers,
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            profile = json.loads(response.read().decode("utf-8"))
            return profile
    except Exception as e:
        raise AuthenticationModuleError(f"OAuth2 profile fetch failed: {str(e)}")


def get_or_create_user(provider: str, profile: dict) -> Any:
    """
    Resolve remote profile to a local User instance.
    First checks linked SocialAccount.
    Second falls back to matching by email.
    Creates a new User + SocialAccount link if no match is found.
    """
    # 1. Map provider_user_id dynamically from standard keys
    provider_user_id = str(profile.get("sub") or profile.get("id") or "")
    if not provider_user_id:
        raise AuthenticationModuleError("Could not determine provider user ID from profile.")

    provider_name = provider.lower()

    # 1. Match existing SocialAccount first
    from authentication.auth_methods.oauth2.models import SocialAccount
    try:
        social_account = SocialAccount.objects.get(
            provider=provider_name,
            provider_user_id=provider_user_id,
        )
        return social_account.user
    except SocialAccount.DoesNotExist:
        pass

    # 2. Fall back to email match
    email = profile.get("email")
    user = None
    if email:
        User = get_user_model()
        try:
            # SECURITY CONSIDERATION:
            # Matching by email assumes that the remote provider has verified
            # the ownership of the email address prior to providing it in the claim.
            # Google / GitHub OpenID Connect profiles verify emails.
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            pass

    # 3. Create a new User if no match exists
    if not user:
        User = get_user_model()
        # Derive a unique username
        raw_username = (
            profile.get("preferred_username")
            or profile.get("login")
            or (email.split("@")[0] if email else f"user_{provider_user_id}")
        )
        # Ensure name conforms to alphanumeric constraint
        base_username = "".join(c for c in raw_username if c.isalnum() or c in "._-")
        if not base_username:
            base_username = f"user_{provider_name}"

        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email or "",
        )
        user.set_unusable_password()
        user.save()

    # Create link to SocialAccount
    SocialAccount.objects.create(
        user=user,
        provider=provider_name,
        provider_user_id=provider_user_id,
    )

    return user


def issue_final_credential(user: Any, request: Any, *, issuer: Optional[str] = None) -> dict:
    """
    Dynamically hand off authorization results to issue the final credential:
    session, token, or jwt.
    Avoids static imports of other methods to preserve module dependency rules.
    """
    if not issuer:
        issuer = getattr(settings, "OAUTH2_DEFAULT_ISSUER", "session")

    issuer_name = issuer.lower()

    if issuer_name == "session":
        from authentication.auth_methods.session.services import SessionAuthMethod
        user_session = SessionAuthMethod.login(request, user)
        return {
            "issuer": "session",
            "session_id": str(user_session.pk),
            "session_key": user_session.session_key,
        }
    elif issuer_name == "token":
        from authentication.auth_methods.token.services import issue as issue_token
        token = issue_token(user)
        return {
            "issuer": "token",
            "token": token.key,
        }
    elif issuer_name == "jwt":
        from authentication.auth_methods.jwt.services import issue_pair as issue_jwt
        tokens = issue_jwt(user)
        return {
            "issuer": "jwt",
            "access": tokens["access"],
            "refresh": tokens["refresh"],
        }
    else:
        raise AuthenticationModuleError(f"Unsupported OAuth2 issuer option: {issuer_name}")
