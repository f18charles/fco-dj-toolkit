from typing import Any, Set
from django.db.models import QuerySet
from django.contrib.auth import get_user_model

from permissions.models import Permission, Role, RolePermission, UserRole, UserPermission
from permissions.cache import get_user_permissions_from_cache, set_user_permissions_cache


def get_all_permissions_for_user(user: Any) -> Set[str]:
    """
    Resolve the full permission set for user:
    direct active grants + active role assignments (including parent role
    permissions) + wildcard expansion.
    Returns a set of codename strings.
    Uses/populates the per-user permission cache.
    """
    if not hasattr(user, "_permissions_cache"):
        cached = get_user_permissions_from_cache(user)
        if cached is not None:
            user._permissions_cache = cached
        else:
            direct_perms = list(
                UserPermission.objects.filter(user=user)
                .active()
                .values_list("permission__codename", flat=True)
            )

            active_user_roles = (
                UserRole.objects.filter(user=user)
                .active()
                .select_related("role__parent")
            )

            role_ids = []
            parent_ids = []
            for ur in active_user_roles:
                role_ids.append(ur.role_id)
                if ur.role and ur.role.parent_id:
                    parent_ids.append(ur.role.parent_id)

            all_role_ids = set(role_ids) | set(parent_ids)

            role_perms = list(
                RolePermission.objects.filter(role_id__in=all_role_ids)
                .values_list("permission__codename", flat=True)
            )

            user._permissions_cache = set(direct_perms) | set(role_perms)
            set_user_permissions_cache(user, user._permissions_cache)

    expanded_perms = set(user._permissions_cache)

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


from permissions.models import (
    Permission,
    Role,
    RolePermission,
    UserRole,
    UserPermission,
    ObjectPermission,
    ScopedUserRole,
    PermissionGroup,
)
from permissions.exceptions import PermissionsModuleError


def get_active_permission_grants(user: Any) -> QuerySet[UserPermission]:
    """Active (non-expired) direct UserPermission rows for this user."""
    return UserPermission.objects.filter(user=user).active()


def get_object_permissions_for_user(user: Any, *, obj: Any = None) -> QuerySet[ObjectPermission]:
    """
    Active object-level grants for user.
    If obj is provided, filter to that specific object.
    """
    qs = ObjectPermission.objects.filter(user=user).active()
    if obj is not None:
        qs = qs.for_object(obj)
    return qs


def get_users_with_permission_on_object(codename: str, obj: Any) -> QuerySet:
    """Users with active ObjectPermission for (codename, obj)."""
    from permissions.services import ObjectPermissionService
    return ObjectPermissionService.get_users_with_permission_on_object(codename, obj)


def get_scoped_roles_for_user(user: Any, *, scope: Any = None) -> QuerySet[ScopedUserRole]:
    """
    Active ScopedUserRole assignments for user.
    If scope is provided, filter to that scope.
    """
    qs = ScopedUserRole.objects.filter(user=user).active()
    if scope is not None:
        qs = qs.for_scope(scope)
    return qs


def get_users_with_scoped_role(role_name: str, scope: Any) -> QuerySet:
    """Users with an active ScopedUserRole for (role_name, scope)."""
    User = get_user_model()
    active = ScopedUserRole.objects.filter(role__name=role_name).for_scope(scope).active()
    return User.objects.filter(pk__in=active.values_list("user_id", flat=True))


def get_expired_object_permissions() -> QuerySet[ObjectPermission]:
    """All expired ObjectPermission rows. For clean_expired_assignments command."""
    return ObjectPermission.objects.expired()


def get_expired_scoped_role_assignments() -> QuerySet[ScopedUserRole]:
    """All expired ScopedUserRole rows. For clean_expired_assignments command."""
    return ScopedUserRole.objects.expired()


def get_permission_groups() -> QuerySet[PermissionGroup]:
    """All PermissionGroup records, ordered by name."""
    return PermissionGroup.objects.all().order_by("name")


def get_permission_group_by_name(name: str) -> PermissionGroup:
    """
    Raises:
        PermissionsModuleError: if not found.
    """
    try:
        return PermissionGroup.objects.get(name=name)
    except PermissionGroup.DoesNotExist:
        raise PermissionsModuleError(f"Permission group '{name}' not found.")

