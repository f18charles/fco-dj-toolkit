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
- `has_permission(*, user, codename: str, obj=None, scope=None) -> bool`
  Evaluates runtime authorization checking superuser bypass, object permissions (if obj provided), scoped roles (if scope provided), direct grants, role/parent inheritance, and wildcards.
- `has_any_permission(*, user, codenames: list[str]) -> bool`
  Returns True if the user holds at least one of the specified permission codenames.
- `has_all_permissions(*, user, codenames: list[str]) -> bool`
  Returns True if the user holds every specified permission codename.

### `ObjectPermissionService`

- `grant(*, user, codename: str, obj, granted_by=None, expires_at=None) -> ObjectPermission`
  Grants a specific permission to a user on a target model instance `obj`.
- `revoke(*, user, codename: str, obj) -> None`
  Revokes an object-level permission from a user.
- `has_object_permission(*, user, codename: str, obj) -> bool`
  Pure object-level permission check. Returns False on any missing grant or error without raising.
- `get_users_with_permission_on_object(codename: str, obj) -> QuerySet`
  Returns users with an active object-level grant for `codename` on `obj`.
- `get_objects_user_can_access(user, codename: str, model_class) -> QuerySet`
  Returns a queryset of `model_class` instances that `user` has `codename` permission on via `ObjectPermission`.

### `ScopedPermissionService`

- `assign_scoped_role(*, user, role_name: str, scope, granted_by=None, expires_at=None) -> ScopedUserRole`
  Assigns a role to a user scoped to an arbitrary target model instance `scope`.
- `revoke_scoped_role(*, user, role_name: str, scope) -> None`
  Revokes a scoped role assignment.
- `get_scoped_roles_for_user(*, user, scope) -> QuerySet[ScopedUserRole]`
  Returns active scoped role assignments for a user within a scope.
- `get_all_permissions_for_user_in_scope(*, user, scope) -> set[str]`
  Resolves all permissions granted to a user within a scope (scoped roles + parent permissions + wildcards).

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
- `get_object_permissions_for_user(user, *, obj=None) -> QuerySet[ObjectPermission]`
  Returns active object-level grants for a user (optionally filtered by target object).
- `get_users_with_permission_on_object(codename: str, obj) -> QuerySet`
  Returns users with active object permissions for (codename, obj).
- `get_scoped_roles_for_user(user, *, scope=None) -> QuerySet[ScopedUserRole]`
  Returns active scoped role assignments for a user (optionally filtered by scope).
- `get_users_with_scoped_role(role_name: str, scope) -> QuerySet`
  Returns users holding an active scoped role for (role_name, scope).
- `get_expired_object_permissions() -> QuerySet[ObjectPermission]`
  Returns expired ObjectPermission records.
- `get_expired_scoped_role_assignments() -> QuerySet[ScopedUserRole]`
  Returns expired ScopedUserRole records.
- `get_permission_groups() -> QuerySet[PermissionGroup]`
  Returns all PermissionGroup instances ordered by name.
- `get_permission_group_by_name(name: str) -> PermissionGroup`
  Retrieves a PermissionGroup by name or raises `PermissionsModuleError`.

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
- `object_permission_required(codename: str, get_object_func=None, raise_exception: bool = True)`
  View decorator enforcing an object-level permission check on a target object resolved from request arguments.
- `scoped_permission_required(codename: str, get_scope_func, raise_exception: bool = True)`
  View decorator enforcing a scoped permission check on a scope object resolved from `get_scope_func`.

---

## Class-Based View Mixins

- `PermissionRequiredMixin`
  CBV mixin checking `required_permission` on dispatch.
- `RoleRequiredMixin`
  CBV mixin checking `required_role` on dispatch.
- `AnyPermissionRequiredMixin`
  CBV mixin checking `required_permissions` (any) on dispatch.
- `ObjectPermissionRequiredMixin`
  CBV mixin checking object permission on dispatch (calls `get_permission_object()` which defaults to `self.get_object()`).
- `ScopedPermissionRequiredMixin`
  CBV mixin checking scoped permission on dispatch (requires implementing `get_permission_scope()`).

---

## DRF Permission Classes

- `HasPermission`
  DRF permission class evaluating `required_permission` or `HasPermission.for_codename(codename)`.
- `HasRole`
  DRF permission class evaluating `required_role` or `HasRole.for_role(role_name)`.
- `HasAnyPermission`
  DRF permission class evaluating `required_permissions` (any).
- `HasObjectPermission`
  DRF permission class evaluating `required_permission` on object instances in `has_object_permission()`.
- `HasScopedPermission`
  DRF permission class evaluating scoped permissions using `view.get_permission_scope()`.

---

## Template Tags (`{% load permissions_tags %}`)

- `{% has_permission request.user "codename" as var %}`
- `{% has_role request.user "role_name" as var %}`
- `{% has_object_permission request.user "codename" obj as var %}`
- `{% has_any_permission request.user "perm1,perm2" as var %}`

---

## Management Command

- `python manage.py clean_expired_assignments [--dry-run] [--older-than DAYS]`
  Cleans up expired assignments across `UserRole`, `UserPermission`, `ScopedUserRole`, and `ObjectPermission`.

