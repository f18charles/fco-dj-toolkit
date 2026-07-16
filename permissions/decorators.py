import inspect
from functools import wraps
from typing import Any, Callable, List

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from asgiref.sync import sync_to_async

from permissions.services import PermissionService


def _handle_unauthorized(request: Any, raise_exception: bool) -> HttpResponse:
    """Helper to raise PermissionDenied or redirect to LOGIN_URL."""
    if raise_exception:
        raise PermissionDenied()
    return redirect_to_login(request.get_full_path())


def permission_required(codename: str, raise_exception: bool = True) -> Callable:
    """
    Decorator for function-based views.
    If user lacks the permission:
      - raise_exception=True: raises PermissionDenied (Django's HTTP 403)
      - raise_exception=False: redirects to settings.LOGIN_URL
    Works with both regular views and async views.
    """
    def decorator(view_func: Callable) -> Callable:
        if inspect.iscoroutinefunction(view_func):
            @wraps(view_func)
            async def async_wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
                has_perm = await sync_to_async(PermissionService.has_permission)(
                    user=request.user, codename=codename
                )
                if not has_perm:
                    return _handle_unauthorized(request, raise_exception)
                return await view_func(request, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(view_func)
            def sync_wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
                if not PermissionService.has_permission(user=request.user, codename=codename):
                    return _handle_unauthorized(request, raise_exception)
                return view_func(request, *args, **kwargs)
            return sync_wrapper
    return decorator


def role_required(role_name: str, raise_exception: bool = True) -> Callable:
    """
    Decorator for function-based views.
    Same raise_exception behavior as permission_required.
    """
    def decorator(view_func: Callable) -> Callable:
        if inspect.iscoroutinefunction(view_func):
            @wraps(view_func)
            async def async_wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
                from permissions.selectors import get_roles_for_user

                def check_role():
                    roles = get_roles_for_user(request.user)
                    return roles.filter(name=role_name).exists()

                has_role = await sync_to_async(check_role)()
                if not has_role:
                    return _handle_unauthorized(request, raise_exception)
                return await view_func(request, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(view_func)
            def sync_wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
                from permissions.selectors import get_roles_for_user
                roles = get_roles_for_user(request.user)
                if not roles.filter(name=role_name).exists():
                    return _handle_unauthorized(request, raise_exception)
                return view_func(request, *args, **kwargs)
            return sync_wrapper
    return decorator


def any_permission_required(codenames: List[str], raise_exception: bool = True) -> Callable:
    """
    Passes if user has AT LEAST ONE of the given codenames.
    """
    def decorator(view_func: Callable) -> Callable:
        if inspect.iscoroutinefunction(view_func):
            @wraps(view_func)
            async def async_wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
                has_perm = await sync_to_async(PermissionService.has_any_permission)(
                    user=request.user, codenames=codenames
                )
                if not has_perm:
                    return _handle_unauthorized(request, raise_exception)
                return await view_func(request, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(view_func)
            def sync_wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
                if not PermissionService.has_any_permission(user=request.user, codenames=codenames):
                    return _handle_unauthorized(request, raise_exception)
                return view_func(request, *args, **kwargs)
            return sync_wrapper
    return decorator


def all_permissions_required(codenames: List[str], raise_exception: bool = True) -> Callable:
    """
    Passes only if user has ALL of the given codenames.
    """
    def decorator(view_func: Callable) -> Callable:
        if inspect.iscoroutinefunction(view_func):
            @wraps(view_func)
            async def async_wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
                has_perm = await sync_to_async(PermissionService.has_all_permissions)(
                    user=request.user, codenames=codenames
                )
                if not has_perm:
                    return _handle_unauthorized(request, raise_exception)
                return await view_func(request, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(view_func)
            def sync_wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
                if not PermissionService.has_all_permissions(user=request.user, codenames=codenames):
                    return _handle_unauthorized(request, raise_exception)
                return view_func(request, *args, **kwargs)
            return sync_wrapper
    return decorator
