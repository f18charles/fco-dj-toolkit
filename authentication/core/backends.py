from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import MultipleObjectsReturned
from django.db import models


class EmailOrUsernameBackend(ModelBackend):
    """
    Authentication backend that allows logging in using either a username
    or an email address (case-insensitive on email).
    """

    def authenticate(self, request, username=None, password=None, **kwargs) -> Any | None:
        User = get_user_model()
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        if not username or not password:
            return None

        try:
            # Query by username exactly OR by email (case-insensitive)
            user = User.objects.get(
                models.Q(username=username) | models.Q(email__iexact=username)
            )
        except User.DoesNotExist:
            # Run set_password to keep authentication timing consistent
            # and prevent user enumeration.
            User().set_password(password)
            return None
        except MultipleObjectsReturned:
            # Fail closed in case of ambiguity
            return None

        # Verify password. We don't check user_can_authenticate(user) here
        # to allow AuthService to handle AccountInactiveError explicitly.
        if user.check_password(password):
            return user

        return None
