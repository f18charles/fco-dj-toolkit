from typing import Any, Set
from django.db.models import QuerySet
from django.contrib.auth import get_user_model

from permissions.models import Permission, Role, RolePermission, UserRole, UserPermission
from permissions.services import PermissionService


def get_all_permissions_for_user(user: Any) -> Set[str]:
    """
    Resolve the full permission set for user:
    direct active grants + active role assignments (including parent role
    permissions) + wildcard expansion.
    Returns a set of codename strings.
    Uses/populates the per-user permission cache.
    """
    # Trigger permission check or cache population
    # Calling has_permission with a dummy/non-existent permission is a safe way
    # to populate the cache if not already present.
    PermissionService.has_permission(user=user, codename="_dummy.cache_populator")

    cached_perms = getattr(user, "_permissions_cache", set())
    expanded_perms = set(cached_perms)

    # Perform wildcard expansion
    for perm in list(expanded_perms):
        if perm.endswith(".*"):
            prefix = perm[:-1]  # e.g., "posts."
            matching = Permission.objects.filter(codename__startswith=prefix).values_list(
                "codename", flat=True
            )
            expanded_perms.update(matching)

    return expanded_perms


def get_roles_for_user(user: Any) -> QuerySet[Role]:
    """Active roles assigned to user (respects expires_at)."""
    active_user_roles = UserRole.objects.filter(user=user).active()
    return Role.objects.filter(id__in=active_user_roles.values_list("role_id", flat=True))


def get_permissions_for_role(role: Role) -> QuerySet[Permission]:
    """All permissions directly assigned to this role (NOT inherited)."""
    return Permission.objects.filter(role_permissions__role=role)


def get_inherited_permissions_for_role(role: Role) -> QuerySet[Permission]:
    """Permissions inherited from the parent role, if any."""
    if role.parent_id:
        return Permission.objects.filter(role_permissions__role_id=role.parent_id)
    return Permission.objects.none()


def get_all_permissions_for_role(role: Role) -> Set[str]:
    """Union of direct + inherited permissions for this role."""
    direct = set(
        Permission.objects.filter(role_permissions__role=role).values_list(
            "codename", flat=True
        )
    )
    if role.parent_id:
        inherited = set(
            Permission.objects.filter(
                role_permissions__role_id=role.parent_id
            ).values_list("codename", flat=True)
        )
        return direct | inherited
    return direct


def get_users_with_role(role_name: str) -> QuerySet:
    """Users who currently have an active assignment of this role."""
    User = get_user_model()
    active_user_roles = UserRole.objects.filter(role__name=role_name).active()
    return User.objects.filter(id__in=active_user_roles.values_list("user_id", flat=True))


def get_users_with_permission(codename: str) -> QuerySet:
    """
    Users who have this permission via any path (direct grant or role).
    Best-effort - does not evaluate wildcard grants (those are
    runtime-only). Documents this limitation in its docstring.
    """
    User = get_user_model()

    # 1. Users with active direct permission
    direct_users = (
        UserPermission.objects.filter(permission__codename=codename)
        .active()
        .values_list("user_id", flat=True)
    )

    # 2. Roles with this permission (directly assigned)
    roles_with_perm = RolePermission.objects.filter(
        permission__codename=codename
    ).values_list("role_id", flat=True)

    # 3. Roles whose parent has this permission
    roles_with_parent_perm = Role.objects.filter(
        parent_id__in=roles_with_perm
    ).values_list("id", flat=True)

    # Combine roles
    all_role_ids = set(roles_with_perm) | set(roles_with_parent_perm)

    # 4. Users with active assignments of any of these roles
    role_users = (
        UserRole.objects.filter(role_id__in=all_role_ids)
        .active()
        .values_list("user_id", flat=True)
    )

    # Combine user IDs
    all_user_ids = set(direct_users) | set(role_users)

    return User.objects.filter(id__in=all_user_ids)


def get_active_role_assignments(user: Any) -> QuerySet[UserRole]:
    """Active (non-expired) UserRole rows for this user."""
    return UserRole.objects.filter(user=user).active()


def get_expired_role_assignments() -> QuerySet[UserRole]:
    """All expired UserRole rows across all users. For cleanup tasks."""
    return UserRole.objects.expired()


def get_active_permission_grants(user: Any) -> QuerySet[UserPermission]:
    """Active (non-expired) direct UserPermission rows for this user."""
    return UserPermission.objects.filter(user=user).active()
