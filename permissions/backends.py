from typing import Any
from django.conf import settings

from permissions.services import PermissionService
from permissions.selectors import get_all_permissions_for_user


class RBACBackend:
    """
    Custom auth backend that bridges this module's RBAC system into
    Django's standard user.has_perm() interface.

    Add to AUTHENTICATION_BACKENDS in settings:

        AUTHENTICATION_BACKENDS = [
            "django.contrib.auth.backends.ModelBackend",
            "permissions.backends.RBACBackend",
        ]

    This backend answers only has_perm() / has_perms() calls.
    It does NOT handle authentication (login/password) - that's
    authentication.core.backends.EmailOrUsernameBackend.
    """

    def authenticate(self, request: Any, **kwargs: Any) -> None:
        """This backend never authenticates."""
        return None

    def has_perm(self, user_obj: Any, perm: str, obj: Any = None) -> bool:
        """
        Called by user.has_perm(). Routes to PermissionService.has_permission().
        obj is ignored in v1 (object-level permissions are v2).
        """
        return PermissionService.has_permission(user=user_obj, codename=perm)

    def has_module_perms(self, user_obj: Any, app_label: str) -> bool:
        """
        Return True if user has any permission whose codename starts with
        app_label + ".". Used by Django admin to decide whether to show
        an app in the admin index.
        """
        if user_obj is None or getattr(user_obj, "is_anonymous", True) or not getattr(user_obj, "is_authenticated", False):
            return False

        bypass = getattr(settings, "PERMISSIONS_SUPERUSER_BYPASS", True)
        if bypass and getattr(user_obj, "is_superuser", False):
            return True

        perms = get_all_permissions_for_user(user_obj)
        prefix = f"{app_label}."
        return any(p.startswith(prefix) for p in perms)
