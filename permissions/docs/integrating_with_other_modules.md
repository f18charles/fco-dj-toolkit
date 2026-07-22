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

## Future v2 Extension: `organizations`

In v2, multi-tenancy and organization-scoped permissions will be introduced. The `permissions` module will be extended by adding optional scoping parameters (e.g. `organization_id`) to `UserRole` and `UserPermission` without breaking the v1 core API contracts.

---

## Decoupling `authentication` and `permissions`

`authentication` and `permissions` maintain strict separation of concerns:
- **`authentication`:** Solves identity ("Who are you?"), handling credentials, sessions, tokens, and multi-factor verification.
- **`permissions`:** Solves access control ("What are you allowed to do?"), managing roles, permission codenames, and evaluation logic.

Neither module imports private internals of the other; `permissions` references the user model via `settings.AUTH_USER_MODEL`.
