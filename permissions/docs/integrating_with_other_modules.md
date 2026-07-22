# Integrating with Other Modules

## Registering Permissions from Consuming Modules

Consuming modules (such as `posts` or `reports`) declare their required permissions in their Django `AppConfig.ready()` method using `PermissionRegistry`:

```python
# posts/apps.py
from django.apps import AppConfig

class PostsConfig(AppConfig):
    name = "posts"

    def ready(self):
        from permissions.registry import registry
        registry.register(
            codename="posts.edit",
            name="Can edit posts",
            module="posts",
            description="Allows editing existing posts",
        )
        registry.register(
            codename="posts.delete",
            name="Can delete posts",
            module="posts",
        )
```

At application startup, `PermissionsConfig.ready()` calls `registry.sync()`, syncing all in-memory declarations to the database idempotently.

---

## Connecting Signals to `audit_logs`

The `permissions` module emits decoupled signals for auditing security and access control changes without importing or depending on `audit_logs`:

```python
# audit_logs/receivers.py
from django.dispatch import receiver
from permissions.signals import role_assigned, permission_granted_to_user

@receiver(role_assigned)
def log_role_assigned(sender, user, role, granted_by, **kwargs):
    AuditLogService.log_event(
        action="role_assigned",
        target=f"user:{user.pk}",
        actor=granted_by,
        context={"role": role.name},
    )

@receiver(permission_granted_to_user)
def log_permission_granted_to_user(sender, user, permission, granted_by, **kwargs):
    AuditLogService.log_event(
        action="permission_granted_to_user",
        target=f"user:{user.pk}",
        actor=granted_by,
        context={"permission": permission.codename},
    )
```

---

---

## Integrating with Object-Level Permissions

Consuming content modules (e.g. `posts`, `documents`) use `ObjectPermissionService` to grant permissions on specific model instances:

```python
from permissions.services import ObjectPermissionService

# Granting permission on a post instance
ObjectPermissionService.grant(
    user=author,
    codename="posts.edit",
    obj=post_instance,
    granted_by=admin_user,
)

# Checking object permission in views/services
can_edit = ObjectPermissionService.has_object_permission(
    user=request.user,
    codename="posts.edit",
    obj=post_instance,
)
```

---

## Integrating with `organizations` (Scoped Roles)

When an `organizations` module is created, organization-scoped roles will use `ScopedPermissionService`:

```python
from permissions.services import ScopedPermissionService

# Assigning a role scoped to an organization instance
ScopedPermissionService.assign_scoped_role(
    user=member,
    role_name="organization_admin",
    scope=organization_instance,
    granted_by=owner,
)
```

---

## Audit Integration (`permissions/audit.py`)

The `permissions/audit.py` file provides copy-paste ready signal receiver templates for connecting all v1 and v2 permission signals to an `audit_logs` module.

---

## Decoupling `authentication` and `permissions`

`authentication` and `permissions` maintain strict separation of concerns:
- **`authentication`:** Solves identity ("Who are you?"), handling credentials, sessions, tokens, and multi-factor verification.
- **`permissions`:** Solves access control ("What are you allowed to do?"), managing roles, permission codenames, and evaluation logic.

Neither module imports private internals of the other; `permissions` references the user model via `settings.AUTH_USER_MODEL`.
