"""
Services: the module's business-logic layer.

All user lifecycle operations that involve more than a single ORM
write (validation, state checks, side effects) belong here, not in
views, forms, or signal handlers. Views should call into
`UserService` rather than manipulating the `User` model directly.
"""
from __future__ import annotations

import uuid
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction

from users.exceptions import (
    EmailAlreadyExistsError,
    UserAlreadyActiveError,
    UserAlreadyInactiveError,
)
from users.selectors import get_user_by_id
from users.validators import validate_unique_email, ValidationError

User = get_user_model()


class UserService:
    """Encapsulates business logic for creating and managing users."""

    @staticmethod
    @transaction.atomic
    def create_user(
        *,
        username: str,
        email: str,
        password: str,
        **extra_fields: Any,
    ) -> User:
        """
        Create and persist a new user.

        Args:
            username: Unique login name for the user.
            email: Unique email address.
            password: Plain-text password (will be hashed).
            **extra_fields: Any additional model fields (e.g. first_name).

        Returns:
            The newly created User instance.

        Raises:
            EmailAlreadyExistsError: if the email is already taken.
        """
        try:
            validate_unique_email(email, User)
        except ValidationError as exc:
            raise EmailAlreadyExistsError(str(exc)) from exc

        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )

    @staticmethod
    @transaction.atomic
    def deactivate_user(*, user_id: uuid.UUID | str) -> User:
        """
        Deactivate a user (sets `is_active=False`).

        Raises:
            UserNotFoundError: if no such user exists.
            UserAlreadyInactiveError: if the user is already inactive.
        """
        user = get_user_by_id(user_id)
        if not user.is_active:
            raise UserAlreadyInactiveError(f"User {user_id} is already inactive.")

        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        return user

    @staticmethod
    @transaction.atomic
    def activate_user(*, user_id: uuid.UUID | str) -> User:
        """
        Activate a user (sets `is_active=True`).

        Raises:
            UserNotFoundError: if no such user exists.
            UserAlreadyActiveError: if the user is already active.
        """
        user = get_user_by_id(user_id)
        if user.is_active:
            raise UserAlreadyActiveError(f"User {user_id} is already active.")

        user.is_active = True
        user.save(update_fields=["is_active", "updated_at"])
        return user

    @staticmethod
    @transaction.atomic
    def update_profile(*, user_id: uuid.UUID | str, **fields: Any) -> User:
        """
        Update non-sensitive profile fields (e.g. first_name, last_name, avatar).

        Email and password changes are intentionally excluded here;
        use `change_email` for email since it has its own validation
        rules, and Django's built-in password-change flow for
        passwords.

        Raises:
            UserNotFoundError: if no such user exists.
        """
        protected_fields = {"email", "password", "id", "pk", "is_staff", "is_superuser"}
        user = get_user_by_id(user_id)

        update_fields: list[str] = []
        for field, value in fields.items():
            if field in protected_fields:
                continue
            setattr(user, field, value)
            update_fields.append(field)

        if update_fields:
            update_fields.append("updated_at")
            user.save(update_fields=update_fields)

        return user

    @staticmethod
    @transaction.atomic
    def change_email(*, user_id: uuid.UUID | str, new_email: str) -> User:
        """
        Change a user's email address.

        Raises:
            UserNotFoundError: if no such user exists.
            EmailAlreadyExistsError: if `new_email` is already taken.
        """
        user = get_user_by_id(user_id)

        try:
            validate_unique_email(new_email, User, exclude_pk=user.pk)
        except ValidationError as exc:
            raise EmailAlreadyExistsError(str(exc)) from exc

        user.email = new_email
        user.save(update_fields=["email", "updated_at"])
        return user
