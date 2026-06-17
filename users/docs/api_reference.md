# API Reference

Detailed reference for the public interfaces of the `users` module.
For installation and quick-start usage, see the top-level `README.md`.

## `users.services.UserService`

All methods are `@staticmethod` and use keyword-only arguments.

### `create_user(*, username, email, password, **extra_fields)`

Creates and persists a new `User`. Validates email uniqueness before
writing to the database.

- **Returns:** the created `User` instance.
- **Raises:** `EmailAlreadyExistsError` if `email` is already taken.

### `deactivate_user(*, user_id)`

Sets `is_active=False` on the target user.

- **Returns:** the updated `User` instance.
- **Raises:** `UserNotFoundError`, `UserAlreadyInactiveError`.

### `activate_user(*, user_id)`

Sets `is_active=True` on the target user.

- **Returns:** the updated `User` instance.
- **Raises:** `UserNotFoundError`, `UserAlreadyActiveError`.

### `update_profile(*, user_id, **fields)`

Updates arbitrary non-protected fields (e.g. `first_name`, `last_name`,
`avatar`). Silently ignores `email`, `password`, `is_staff`, and
`is_superuser` — use `change_email` or Django's password-change flow
for those.

- **Returns:** the updated `User` instance.
- **Raises:** `UserNotFoundError`.

### `change_email(*, user_id, new_email)`

Validates uniqueness (excluding the user's own current row) and
updates the email address.

- **Returns:** the updated `User` instance.
- **Raises:** `UserNotFoundError`, `EmailAlreadyExistsError`.

## `users.selectors`

Module-level functions, not a class — import individually:

```python
from users.selectors import get_user_by_id, get_active_users
```

| Function | Returns | Raises |
| --- | --- | --- |
| `get_user_by_id(user_id)` | `User` | `UserNotFoundError` |
| `get_user_by_email(email)` | `User` | `UserNotFoundError` |
| `get_active_users()` | `QuerySet[User]` | — |
| `get_inactive_users()` | `QuerySet[User]` | — |
| `get_staff_users()` | `QuerySet[User]` | — |
| `get_users_by_ids(user_ids)` | `QuerySet[User]` | — |

## `users.managers`

- `UserQuerySet`: `.active()`, `.inactive()`, `.staff()` — chainable.
- `UserManager`: extends `BaseUserManager` with `create_user`,
  `create_superuser`, plus proxies to the queryset filters above.

## `users.validators`

| Function | Purpose |
| --- | --- |
| `validate_username(value)` | Enforces the 3-30 char username policy. |
| `validate_unique_email(email, model, *, exclude_pk=None)` | Raises if email is taken by another row. |
| `validate_avatar_image(file)` | Enforces content-type and size limits on avatar uploads. |

## `users.exceptions`

```
UserModuleError
├── UserNotFoundError
├── EmailAlreadyExistsError
└── InvalidUserStateError
    ├── UserAlreadyActiveError
    └── UserAlreadyInactiveError
```

## `users.signals`

- `user_created(sender, user)` — sent once, right after creation.
- `user_updated(sender, user, updated_fields)` — sent on every
  subsequent save. `updated_fields` is currently always `None`; the
  signal exists primarily as a stable extension point.

## `users.permissions`

| Function | Purpose |
| --- | --- |
| `is_owner_or_staff(user, target)` | True if `user` is `target`, or staff/superuser. |
| `can_deactivate_user(user, target)` | Alias of `is_owner_or_staff`. |
| `can_change_email(user, target)` | True if `user` is `target`, or a superuser. |
| `IsSelfOrStaff` | Object-level permission class, DRF-compatible. |
