"""
Selectors: the module's read-only query layer.

Selectors encapsulate "how do I read this data" so views, services,
and other modules never write raw `.objects.filter(...)` calls
themselves. Keeping reads here also gives a single place to optimize
queries (e.g. `select_related`) later without touching call sites.
"""
from __future__ import annotations

import uuid
from typing import Iterable

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from users.exceptions import UserNotFoundError

User = get_user_model()


def get_user_by_id(user_id: uuid.UUID | str) -> User:
    """
    Return a single user by primary key.

    Raises:
        UserNotFoundError: if no user with that id exists.
    """
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist as exc:
        raise UserNotFoundError(f"No user found with id={user_id}.") from exc


def get_user_by_email(email: str) -> User:
    """
    Return a single user by email address (case-insensitive).

    Raises:
        UserNotFoundError: if no user with that email exists.
    """
    try:
        return User.objects.get(email__iexact=email)
    except User.DoesNotExist as exc:
        raise UserNotFoundError(f"No user found with email={email}.") from exc


def get_active_users() -> QuerySet:
    """Return a queryset of all active users."""
    return User.objects.active()


def get_inactive_users() -> QuerySet:
    """Return a queryset of all inactive users."""
    return User.objects.inactive()


def get_staff_users() -> QuerySet:
    """Return a queryset of all staff users."""
    return User.objects.staff()


def get_users_by_ids(user_ids: Iterable[uuid.UUID | str]) -> QuerySet:
    """Return a queryset of users whose primary key is in `user_ids`."""
    return User.objects.filter(pk__in=list(user_ids))
