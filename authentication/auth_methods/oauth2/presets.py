from authentication.auth_methods.oauth2.providers import OAuth2ProviderConfig


def google_preset(client_id: str, client_secret: str) -> OAuth2ProviderConfig:
    """
    Preset configuration for Google OAuth2.
    """
    return OAuth2ProviderConfig(
        client_id=client_id,
        client_secret=client_secret,
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        userinfo_url="https://www.googleapis.com/oauth2/v3/userinfo",
        scopes=["openid", "email", "profile"],
    )


def github_preset(client_id: str, client_secret: str) -> OAuth2ProviderConfig:
    """
    Preset configuration for GitHub OAuth2.
    """
    return OAuth2ProviderConfig(
        client_id=client_id,
        client_secret=client_secret,
        authorize_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        userinfo_url="https://api.github.com/user",
        scopes=["read:user", "user:email"],
    )
