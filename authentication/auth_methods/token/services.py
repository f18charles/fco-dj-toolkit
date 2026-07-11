from typing import Any
from rest_framework.authtoken.models import Token


def issue(user: Any) -> Token:
    """
    Get or create an API token for the user.
    """
    token, _ = Token.objects.get_or_create(user=user)
    return token


def rotate(user: Any) -> Token:
    """
    Delete any existing token and create a new one.
    """
    Token.objects.filter(user=user).delete()
    return Token.objects.create(user=user)


def revoke(user: Any) -> None:
    """
    Delete the user's token.
    """
    Token.objects.filter(user=user).delete()
