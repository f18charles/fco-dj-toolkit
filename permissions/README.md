# Permissions Module

## Purpose

The `permissions` module provides a flexible, database-backed Role-Based Access Control (RBAC) system for `fco-dj-kit`. It decouples roles and permissions from Django's `ContentType` system, supporting custom codenames, single-level role inheritance, wildcard permission matching, direct permission grants, and expiring assignments while remaining fully transparent to Django's standard `user.has_perm()` interface.

---

## Installation

Add `"common"`, `"users"`, and `"permissions"` to your `INSTALLED_APPS` setting in `settings.py`:

```python
INSTALLED_APPS = [
    ...
    "common",
    "users",
    "permissions",
    ...
]

AUTH_USER_MODEL = "users.User"
```

---

## Quick Start

### Assigning a Role & Direct Permission
```python
from permissions.services import RoleService, PermissionService

# Create a role and assign it to a user
RoleService.create_role(name="editor")
RoleService.assign_role(user=user, role_name="editor")

# Create a permission and grant it directly
PermissionService.create_permission(codename="posts.publish", name="Can publish posts")
PermissionService.grant_permission_to_user(user=user, codename="posts.publish")
```

### Enforcing Permissions in Views
```python
from permissions.decorators import permission_required

@permission_required("posts.publish")
def publish_post_view(request):
    return HttpResponse("Published")
```

---

## Choosing an Enforcement Method

- **Decorators (`@permission_required`, `@role_required`):** Best for function-based views (FBVs) and async views when quick authorization guards are needed.
- **CBV Mixins (`PermissionRequiredMixin`, `RoleRequiredMixin`):** Ideal for Django class-based views, integrating natively with Django's `AccessMixin`.
- **Helper Functions / Service (`PermissionService.has_permission()`):** Best for conditional business logic inside services, form processing, or custom templates.
- **DRF Permission Classes (`HasPermission`, `HasRole`):** Essential for Django REST Framework views (`APIView`, `ViewSet`) to output clean HTTP 403 Forbidden responses.

---

## Registry

Consuming modules declare permissions during startup in `AppConfig.ready()`:

```python
from permissions.registry import registry

registry.register(
    codename="reports.export",
    name="Can export reports",
    module="reports",
)
```

At startup, `PermissionsConfig.ready()` calls `registry.sync()` to persist declared permissions idempotently in the database.

---

## Configuration

Configure options in `settings.py`:

```python
# If True, superusers bypass permission checks and return True. Default: True.
PERMISSIONS_SUPERUSER_BYPASS = True
```

---

## Backends

To integrate with Django's `user.has_perm()`:

```python
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "permissions.backends.RBACBackend",
]
```

---

## Signals

The module declares the following signals in `permissions.signals`:
- `role_created(role)`
- `role_assigned(user, role, granted_by)`
- `role_revoked(user, role)`
- `permission_created(permission)`
- `permission_granted_to_user(user, permission, granted_by)`
- `permission_revoked_from_user(user, permission)`
- `permission_granted_to_role(role, permission, granted_by)`
- `permission_revoked_from_role(role, permission)`
- `permission_checked(user, codename, result: bool)`

### Example Audit Log Receiver:
```python
from django.dispatch import receiver
from permissions.signals import role_assigned

@receiver(role_assigned)
def audit_role_assignment(sender, user, role, granted_by, **kwargs):
    AuditLogService.log(action="role_assigned", user=user, role=role.name, granted_by=granted_by)
```

---

## What's New in v2

- **Object-Level Permissions (`ObjectPermission` & `ObjectPermissionService`)**: Grant permissions on specific model instances via `GenericForeignKey`.
- **Generic Scope System (`ScopedUserRole` & `ScopedPermissionService`)**: Scope role assignments to any model instance (such as organizations or projects).
- **Display Permission Groups (`PermissionGroup`)**: Name and organize sets of permissions for admin UI display.
- **Cross-Request Caching**: Opt-in Redis-backed caching layer (`permissions.cache`) with instant signal invalidation.
- **Template Tags (`{% load permissions_tags %}`)**: Declarative permission checking tags (`has_permission`, `has_role`, `has_object_permission`, `has_any_permission`).
- **Management Command**: `clean_expired_assignments` for purging expired roles and grants.
- **DRF End-to-End Extensions**: `HasObjectPermission` and `HasScopedPermission` for REST API views.

---

## v2 Usage Examples

### Object-Level Permissions
```python
from permissions.services import ObjectPermissionService

# Grant permission on a specific post object
ObjectPermissionService.grant(user=user, codename="posts.edit", obj=post)

# Check permission on specific object
can_edit = ObjectPermissionService.has_object_permission(user=user, codename="posts.edit", obj=post)
```

### Scoped Roles
```python
from permissions.services import ScopedPermissionService

# Assign a role scoped to an organization instance
ScopedPermissionService.assign_scoped_role(user=user, role_name="editor", scope=org_instance)
```

### Cache Configuration
See [docs/caching.md](file:///D:/FCO/Coding/fco-dj-toolkit/permissions/docs/caching.md) for full setup instructions.
```python
PERMISSIONS_CACHE_BACKEND = "permissions"
PERMISSIONS_CACHE_TTL = 300
```

### Template Tags
Requires `"django.template.context_processors.request"` in `TEMPLATES` settings.
```html
{% load permissions_tags %}

{% has_permission request.user "posts.edit" as can_edit %}
{% if can_edit %}<a href="/edit/">Edit</a>{% endif %}

{% has_object_permission request.user "posts.edit" post as can_edit_post %}
{% if can_edit_post %}<a href="/posts/{{ post.pk }}/edit/">Edit Post</a>{% endif %}
```

### Cleaning Expired Assignments (Cron Example)
Run daily via scheduled task:
```bash
python manage.py clean_expired_assignments --older-than 7
```

---

## v3 Roadmap

- **Explicit Deny Rules**: Support for negative permission overrides overriding grants.
- **Multiple Role Inheritance**: Support for role graphs inheriting from multiple parent roles.
- **Temporal Permission Snapshots**: Point-in-time security audit log snapshots.
