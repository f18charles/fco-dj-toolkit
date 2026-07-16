try:
    from rest_framework.permissions import BasePermission
except ImportError:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        "django-rest-framework is required to use this module's DRF components."
    )

from typing import Any, List
from permissions.services import PermissionService


class HasPermission(BasePermission):
    """
    DRF permission class. Set on a view:
        permission_classes = [IsAuthenticated, HasPermission]
        required_permission = "posts.edit"
    Or pass codename at class definition:
        class MyView(APIView):
            permission_classes = [HasPermission.for_codename("posts.edit")]
    """
    required_permission: str = ""

    @classmethod
    def for_codename(cls, codename: str) -> type:
        """Return a subclass with required_permission set."""
        return type(
            f"HasPermission_{codename.replace('.', '_')}",
            (cls,),
            {"required_permission": codename},
        )

    def has_permission(self, request: Any, view: Any) -> bool:
        codename = self.required_permission or getattr(view, "required_permission", "")
        if not codename:
            return False
        return PermissionService.has_permission(user=request.user, codename=codename)


class HasRole(BasePermission):
    """
    DRF permission class to guard based on Role.
    """
    required_role: str = ""

    @classmethod
    def for_role(cls, role_name: str) -> type:
        """Return a subclass with required_role set."""
        return type(
            f"HasRole_{role_name.replace(' ', '_')}",
            (cls,),
            {"required_role": role_name},
        )

    def has_permission(self, request: Any, view: Any) -> bool:
        role_name = self.required_role or getattr(view, "required_role", "")
        if not role_name:
            return False
        from permissions.selectors import get_roles_for_user
        roles = get_roles_for_user(request.user)
        return roles.filter(name=role_name).exists()


class HasAnyPermission(BasePermission):
    """
    DRF permission class to guard based on any of list of permissions.
    """
    required_permissions: List[str] = []

    def has_permission(self, request: Any, view: Any) -> bool:
        codenames = self.required_permissions or getattr(view, "required_permissions", [])
        if not codenames:
            return False
        return PermissionService.has_any_permission(user=request.user, codenames=codenames)
