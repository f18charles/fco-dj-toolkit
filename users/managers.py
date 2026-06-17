"""
Custom manager and queryset for the User model.

Combines Django's BaseUserManager (create_user / create_superuser
semantics) with a custom queryset (active / inactive / staff filters),
so both creation helpers and filtering chains are available from
`User.objects`.
"""
from __future__ import annotations

from typing import Any

from django.contrib.auth.base_user import BaseUserManager
from django.db import models


class UserQuerySet(models.QuerySet):
    """Custom queryset providing common, chainable filters for users."""

    def active(self) -> "UserQuerySet":
        """Return only users with `is_active=True`."""
        return self.filter(is_active=True)

    def inactive(self) -> "UserQuerySet":
        """Return only users with `is_active=False`."""
        return self.filter(is_active=False)

    def staff(self) -> "UserQuerySet":
        """Return only users with `is_staff=True`."""
        return self.filter(is_staff=True)


class UserManager(BaseUserManager.from_queryset(UserQuerySet)):
    """
    Custom manager for the User model.

    Provides Django's expected `create_user` / `create_superuser`
    interface (required for `manage.py createsuperuser` and auth
    backends) plus convenience proxies to the custom queryset filters.
    """

    use_in_migrations = True

    def _create_user(
        self,
        username: str,
        email: str | None,
        password: str | None,
        **extra_fields: Any,
    ):
        if not username:
            raise ValueError("The username must be set.")
        if not email:
            raise ValueError("The email must be set.")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self,
        username: str,
        email: str | None = None,
        password: str | None = None,
        **extra_fields: Any,
    ):
        """Create and save a regular (non-staff, non-superuser) user."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(
        self,
        username: str,
        email: str | None = None,
        password: str | None = None,
        **extra_fields: Any,
    ):
        """Create and save a superuser, enforcing is_staff/is_superuser=True."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, email, password, **extra_fields)

    def active(self) -> "UserQuerySet":
        """Proxy to `UserQuerySet.active`."""
        return self.get_queryset().active()

    def inactive(self) -> "UserQuerySet":
        """Proxy to `UserQuerySet.inactive`."""
        return self.get_queryset().inactive()

    def staff(self) -> "UserQuerySet":
        """Proxy to `UserQuerySet.staff`."""
        return self.get_queryset().staff()
