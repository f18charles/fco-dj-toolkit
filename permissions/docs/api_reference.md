# Permissions API Reference

## Services

### `PermissionService`

- `create_permission(*, codename: str, name: str, module: str = "", description: str = "") -> Permission`
  Creates a Permission object, validating codename format and operating idempotently.
- `get_or_create_permission(codename: str) -> Permission`
  Retrieves or creates a Permission by codename, used internally by registry sync.
- `grant_permission_to_user(*, user, codename: str, granted_by=None, expires_at=None) -> UserPermission`
  Grants a direct permission to a user with an optional expiration timestamp.
- `revoke_permission_from_user(*, user, codename: str) -> None`
  Revokes a direct permission grant from a user.
- `grant_permission_to_role(*, role_name: str, codename: str, granted_by=None) -> RolePermission`
  Assigns a permission to a specified role.
- `revoke_permission_from_role(*, role_name: str, codename: str) -> None`
  Revokes a permission from a specified role.
- `has_permission(*, user, codename: str) -> bool`
  Evaluates runtime authorization checking superuser bypass, direct grants, role/parent inheritance, and wildcards.
- `has_any_permission(*, user, codenames: list[str]) -> bool`
  Returns True if the user holds at least one of the specified permission codenames.
- `has_all_permissions(*, user, codenames: list[str]) -> bool`
  Returns True if the user holds every specified permission codename.

### `RoleService`

- `create_role(*, name: str, description: str = "", parent_name: str | None = None, is_system_role: bool = False) -> Role`
  Creates a new role with optional single-level parent inheritance.
- `assign_role(*, user, role_name: str, granted_by=None, expires_at=None) -> UserRole`
  Assigns a role to a user with optional expiration date and invalidates user cache.
- `revoke_role(*, user, role_name: str) -> None`
  Revokes a role assignment from a user and invalidates user cache.
- `get_user_roles(*, user) -> QuerySet`
  Returns active UserRole assignments for the given user.
- `clone_role(*, source_role_name: str, new_name: str) -> Role`
  Creates a new role copying all permissions from a source role.
- `delete_role(*, role_name: str) -> None`
  Deletes a non-system role.

---

## Selectors

- `get_all_permissions_for_user(user) -> set[str]`
  Resolves the complete active permission codename set for a user.
- `get_roles_for_user(user) -> QuerySet[Role]`
  Returns active Roles currently assigned to a user.
- `get_permissions_for_role(role: Role) -> QuerySet[Permission]`
  Returns permissions directly assigned to a role.
- `get_inherited_permissions_for_role(role: Role) -> QuerySet[Permission]`
  Returns permissions inherited from a role's parent.
- `get_all_permissions_for_role(role: Role) -> set[str]`
  Returns combined direct and inherited permission codenames for a role.
- `get_users_with_role(role_name: str) -> QuerySet`
  Returns users holding an active assignment of the specified role.
- `get_users_with_permission(codename: str) -> QuerySet`
  Returns users holding the specified permission via direct grant or role assignment.
- `get_active_role_assignments(user) -> QuerySet[UserRole]`
  Returns non-expired UserRole instances for a user.
- `get_expired_role_assignments() -> QuerySet[UserRole]`
  Returns all expired UserRole assignments across the system.
- `get_active_permission_grants(user) -> QuerySet[UserPermission]`
  Returns non-expired direct UserPermission instances for a user.

---

## Decorators

- `permission_required(codename: str, raise_exception: bool = True)`
  View decorator enforcing that the user possesses a specific permission.
- `role_required(role_name: str, raise_exception: bool = True)`
  View decorator enforcing that the user possesses a specific role.
- `any_permission_required(codenames: list[str], raise_exception: bool = True)`
  View decorator requiring at least one of the specified permissions.
- `all_permissions_required(codenames: list[str], raise_exception: bool = True)`
  View decorator requiring all of the specified permissions.

---

## Class-Based View Mixins

- `PermissionRequiredMixin`
  CBV mixin checking `required_permission` on dispatch.
- `RoleRequiredMixin`
  CBV mixin checking `required_role` on dispatch.
- `AnyPermissionRequiredMixin`
  CBV mixin checking `required_permissions` (any) on dispatch.

---

## DRF Permission Classes

- `HasPermission`
  DRF permission class evaluating `required_permission` or `HasPermission.for_codename(codename)`.
- `HasRole`
  DRF permission class evaluating `required_role` or `HasRole.for_role(role_name)`.
- `HasAnyPermission`
  DRF permission class evaluating `required_permissions` (any).
