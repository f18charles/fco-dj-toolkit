"""
Permission helpers for the users module.

These are plain functions (framework-agnostic) plus one small
duck-typed class compatible with DRF's `permission_classes`, so the
module stays usable whether or not Django REST Framework is
installed in the consuming project.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model

User = get_user_model()


def is_owner_or_staff(user: User, target: User) -> bool:
    """Return True if `user` is `target` themselves, or is staff/superuser."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return user.pk == target.pk or user.is_staff or user.is_superuser


def can_deactivate_user(user: User, target: User) -> bool:
    """Staff/superusers may deactivate anyone; users may deactivate themselves."""
    return is_owner_or_staff(user, target)


def can_change_email(user: User, target: User) -> bool:
    """Only the user themselves, or a superuser, may change an email."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return user.pk == target.pk or user.is_superuser


class IsSelfOrStaff:
    """
    Object-level permission usable with Django REST Framework:

        from users.permissions import IsSelfOrStaff
        permission_classes = [IsSelfOrStaff]

    Falls back gracefully if DRF is not installed, since it does not
    import anything from `rest_framework` itself (DRF only requires
    `has_object_permission` to be present).
    """

    message = "You do not have permission to act on this user."

    def has_object_permission(self, request, view, obj) -> bool:
        return is_owner_or_staff(request.user, obj)
