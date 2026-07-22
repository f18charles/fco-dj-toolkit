# Permissions Architecture

## Why a Custom Permission Model?

Django's built-in `auth.Permission` system tightly couples permissions to Django's `ContentType` framework (models). While useful for simple CRUD scenarios, this design introduces several limitations for modular Django applications:
- **Tight Coupling to DB Models:** Custom actions (e.g. `reports.export`, `billing.refund`) do not naturally map to Django models.
- **Global Magic Strings:** Default permissions (`app.add_model`) are automatically generated and clutter the namespace.
- **Inheritance & Expiration Limits:** Django's default permissions lack support for role inheritance hierarchies, expiring user assignments, or explicit direct user overrides with expiration dates.

The `permissions` module implements decoupled, first-class `Permission` and `Role` models storing clean dot-notation codenames (e.g., `posts.edit`, `reports.export`).

---

## Permission Resolution Order

When calling `PermissionService.has_permission(user=user, codename=codename)` (or `user.has_perm(codename)`), the resolution occurs in the following sequential order:

1. **Superuser Bypass Check:**
   - If `settings.PERMISSIONS_SUPERUSER_BYPASS` is `True` (default) and `user.is_superuser` is `True`, immediately returns `True`.
2. **Direct Active Grants Check:**
   - Checks `UserPermission` for an active direct grant to `user` for `codename`. Active means `expires_at` is `None` or `expires_at > now()`.
3. **Role Assignments & Inheritance Check:**
   - Evaluates active `UserRole` assignments for `user`.
   - Collects permissions assigned to each active role as well as permissions inherited from each role's `parent` role (single-level inheritance).
4. **Wildcard Permission Matching:**
   - Checks if any granted permission string (direct or via role) is a wildcard pattern (e.g., `posts.*` matching `posts.edit`).

If no matching active grant or wildcard is found, returns `False`.

---

## Cache Strategy & Invalidation

To optimize performance and eliminate redundant database queries per request, the permission set for a user is cached directly on the in-memory user instance attribute (`user._permissions_cache`):
- **Populating Cache:** Evaluated during the first permission check or call to `selectors.get_all_permissions_for_user(user)`.
- **Invalidation Triggers:** Connected via Django `post_save` and `post_delete` signals on `UserRole` and `UserPermission`. When a user's role or direct permission is assigned, modified, or revoked, `user._permissions_cache` is cleared automatically.

---

## Django Authentication Backend Integration (`RBACBackend`)

The `RBACBackend` extends Django's authentication backend system:
- It connects into `AUTHENTICATION_BACKENDS`.
- Intercepts `user.has_perm(perm)` and delegates directly to `PermissionService.has_permission(user=user, codename=perm)`.
- Implements `has_module_perms(user_obj, app_label)` by checking if the user has any permission beginning with `app_label + "."`.
- Does **not** perform user authentication (`authenticate()` always returns `None`), remaining completely decoupled from authentication logic.

---

## v2 Architecture Extensions

### 1. Generic Scope System
The `ScopedUserRole` model allows role assignments to be scoped to any target domain entity (such as projects, workspaces, or organizations) using Django's `GenericForeignKey` (`content_type` + `object_id`).
- It is completely decoupled from future domain modules: any Django model instance can act as a scope object.
- When an `organizations` module is created in the future, `Organization` instances will be passed as the `scope` argument to `ScopedPermissionService` without requiring changes to the permissions system.

### 2. Object-Level Permission Resolution
Object-level permissions (`ObjectPermission`) grant specific codenames on target model instances via `GenericForeignKey`.
- **Pure Object Check**: `ObjectPermissionService.has_object_permission(user=user, codename=codename, obj=obj)` evaluates object-level grants exclusively and does not fall through to global permissions.
- **Combined Check**: `PermissionService.has_permission(user=user, codename=codename, obj=obj)` checks `ObjectPermission` first, and falls through to global permission resolution if no object-level grant exists.

### 3. Cross-Request Cache Layer
v2 introduces an opt-in Redis-backed cross-request cache (`permissions.cache`), which stores resolved global permission sets across HTTP requests while maintaining instant signal-driven invalidation. See `docs/caching.md` for complete details.
