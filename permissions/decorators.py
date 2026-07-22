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


def object_permission_required(
    codename: str, get_object_func: Callable = None, raise_exception: bool = True
) -> Callable:
    """
    Decorator for function-based views that checks an object-level permission.
    """
    def decorator(view_func: Callable) -> Callable:
        def _resolve_obj(request: Any, args: tuple, kwargs: dict) -> Any:
            if get_object_func is not None:
                return get_object_func(request, *args, **kwargs)
            if hasattr(view_func, "get_object"):
                return view_func.get_object(request, *args, **kwargs)
            raise ValueError("No get_object_func provided and view_func has no get_object method.")

        if inspect.iscoroutinefunction(view_func):
            @wraps(view_func)
            async def async_wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
                obj = await sync_to_async(_resolve_obj)(request, args, kwargs)
                has_perm = await sync_to_async(PermissionService.has_permission)(
                    user=request.user, codename=codename, obj=obj
                )
                if not has_perm:
                    return _handle_unauthorized(request, raise_exception)
                return await view_func(request, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(view_func)
            def sync_wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
                obj = _resolve_obj(request, args, kwargs)
                if not PermissionService.has_permission(user=request.user, codename=codename, obj=obj):
                    return _handle_unauthorized(request, raise_exception)
                return view_func(request, *args, **kwargs)
            return sync_wrapper
    return decorator


def scoped_permission_required(
    codename: str, get_scope_func: Callable, raise_exception: bool = True
) -> Callable:
    """
    Decorator for function-based views that checks a permission within a scope.
    """
    def decorator(view_func: Callable) -> Callable:
        if inspect.iscoroutinefunction(view_func):
            @wraps(view_func)
            async def async_wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
                scope = await sync_to_async(get_scope_func)(request, *args, **kwargs)
                has_perm = await sync_to_async(PermissionService.has_permission)(
                    user=request.user, codename=codename, scope=scope
                )
                if not has_perm:
                    return _handle_unauthorized(request, raise_exception)
                return await view_func(request, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(view_func)
            def sync_wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
                scope = get_scope_func(request, *args, **kwargs)
                if not PermissionService.has_permission(user=request.user, codename=codename, scope=scope):
                    return _handle_unauthorized(request, raise_exception)
                return view_func(request, *args, **kwargs)
            return sync_wrapper
    return decorator

