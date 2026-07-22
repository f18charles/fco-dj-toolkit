from typing import Any, Union, List
from django import template

from permissions.services import PermissionService, ObjectPermissionService
from permissions.selectors import get_roles_for_user

register = template.Library()


@register.simple_tag
def has_permission(user: Any, codename: str) -> bool:
    """
    Template tag checking if user has global permission `codename`.
    Usage: {% has_permission request.user "posts.edit" as can_edit %}
    """
    try:
        return PermissionService.has_permission(user=user, codename=codename)
    except Exception:
        return False


@register.simple_tag
def has_role(user: Any, role_name: str) -> bool:
    """
    Template tag checking if user has active role `role_name`.
    Usage: {% has_role request.user "editor" as is_editor %}
    """
    try:
        if user is None or getattr(user, "is_anonymous", True):
            return False
        roles = get_roles_for_user(user)
        return roles.filter(name=role_name).exists()
    except Exception:
        return False


@register.simple_tag
def has_object_permission(user: Any, codename: str, obj: Any) -> bool:
    """
    Template tag checking if user has object-level permission `codename` on `obj`.
    Usage: {% has_object_permission request.user "posts.edit" post as can_edit_post %}
    """
    try:
        return ObjectPermissionService.has_object_permission(user=user, codename=codename, obj=obj)
    except Exception:
        return False


@register.simple_tag
def has_any_permission(user: Any, codenames: Union[str, List[str]]) -> bool:
    """
    Template tag checking if user has at least one of the given permissions.
    Codnames can be a comma-separated string or a list.
    Usage: {% has_any_permission request.user "posts.edit,posts.publish" as can_do_something %}
    """
    try:
        if isinstance(codenames, str):
            c_list = [c.strip() for c in codenames.split(",") if c.strip()]
        else:
            c_list = list(codenames)
        return PermissionService.has_any_permission(user=user, codenames=c_list)
    except Exception:
        return False
