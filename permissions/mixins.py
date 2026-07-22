from typing import Any, List
from django.contrib.auth.mixins import AccessMixin

from permissions.services import PermissionService


class PermissionRequiredMixin(AccessMixin):
    """
    required_permission: str   set on the view class
    Raises PermissionDenied or redirects to login depending on
    raise_exception (inherited from AccessMixin).
    """
    required_permission: str = ""

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if not PermissionService.has_permission(user=request.user, codename=self.required_permission):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class RoleRequiredMixin(AccessMixin):
    """
    required_role: str   set on the view class
    """
    required_role: str = ""

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        from permissions.selectors import get_roles_for_user
        roles = get_roles_for_user(request.user)
        if not roles.filter(name=self.required_role).exists():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AnyPermissionRequiredMixin(AccessMixin):
    """
    required_permissions: list[str]   at least one must be held
    """
    required_permissions: List[str] = []

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if not PermissionService.has_any_permission(user=request.user, codenames=self.required_permissions):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class ObjectPermissionRequiredMixin(AccessMixin):
    """
    CBV mixin enforcing an object-level permission check.
    Override get_permission_object() to specify target object.
    Default calls self.get_object().
    """
    required_permission: str = ""

    def get_permission_object(self) -> Any:
        if hasattr(self, "get_object"):
            return self.get_object()
        raise NotImplementedError("Override get_permission_object()")

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        obj = self.get_permission_object()
        if not PermissionService.has_permission(
            user=request.user, codename=self.required_permission, obj=obj
        ):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class ScopedPermissionRequiredMixin(AccessMixin):
    """
    CBV mixin enforcing a scoped permission check.
    Override get_permission_scope() to specify scope object.
    """
    required_permission: str = ""

    def get_permission_scope(self) -> Any:
        raise NotImplementedError("Override get_permission_scope()")

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        scope = self.get_permission_scope()
        if not PermissionService.has_permission(
            user=request.user, codename=self.required_permission, scope=scope
        ):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

