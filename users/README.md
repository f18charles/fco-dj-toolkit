# users

A reusable, self-contained Django user-management module for the `fco-dj-kit` package.

## Purpose

`users` provides a production-ready foundation for handling users across multiple
Django projects: a custom `User` model (UUID primary key, unique email, avatar),
a manager with common query helpers, a service layer for business logic, a
selectors layer for reads, validators, forms, a customized admin, signals for
lifecycle events, and a small permissions module.

It follows the architectural principles of `fco-dj-kit`:

- Database queries live in `managers.py` / `selectors.py`.
- Business logic lives in `services.py`.
- Input validation lives in `validators.py` / `forms.py`.
- Views (`views.py`) are thin and only handle HTTP concerns.

## Installation

1. Copy (or install) the `users` package into your Django project so it's
   importable as a top-level app, e.g. at the project root next to `manage.py`.

2. Add it to `INSTALLED_APPS` **before** running your first migration:

   ```python
   INSTALLED_APPS = [
       ...
       "django.contrib.auth",
       "django.contrib.contenttypes",
       "users",
   ]
   ```

3. Point Django at the custom user model:

   ```python
   AUTH_USER_MODEL = "users.User"
   ```

4. Run migrations:

   ```bash
   python manage.py makemigrations users
   python manage.py migrate
   ```

> **Note:** `AUTH_USER_MODEL` cannot be changed after the first migration has
> been applied to a project. Install this module before your project has any
> existing user data.

### Dependencies

- Django (4.2+ recommended)
- Pillow (required by `ImageField` for the `avatar` field)

Install with:

```bash
pip install django pillow
```

## Configuration

No required settings beyond `AUTH_USER_MODEL`. Optional integration points:

- **URLs** — include the module's profile/deactivate views:

  ```python
  # project urls.py
  from django.urls import include, path

  urlpatterns = [
      path("users/", include("users.urls")),
  ]
  ```

- **Media** — since `avatar` is an `ImageField`, make sure `MEDIA_ROOT` /
  `MEDIA_URL` are configured as usual for any Django project that serves
  user uploads.

- **Signals** — other modules can subscribe to `users.signals.user_created`
  and `users.signals.user_updated` instead of coupling to `post_save` +
  `sender=User` directly. See the commented examples at the bottom of
  `signals.py`.

## Public API

### `users.services.UserService`

| Method | Description |
| --- | --- |
| `create_user(*, username, email, password, **extra_fields)` | Creates a user. Raises `EmailAlreadyExistsError` if the email is taken. |
| `deactivate_user(*, user_id)` | Sets `is_active=False`. Raises `UserNotFoundError` / `UserAlreadyInactiveError`. |
| `activate_user(*, user_id)` | Sets `is_active=True`. Raises `UserNotFoundError` / `UserAlreadyActiveError`. |
| `update_profile(*, user_id, **fields)` | Updates non-sensitive fields (e.g. `first_name`, `avatar`). Ignores `email`/`password`/permission fields. |
| `change_email(*, user_id, new_email)` | Changes email with uniqueness validation. Raises `EmailAlreadyExistsError`. |

### `users.selectors`

| Function | Description |
| --- | --- |
| `get_user_by_id(user_id)` | Raises `UserNotFoundError` if missing. |
| `get_user_by_email(email)` | Case-insensitive lookup; raises `UserNotFoundError` if missing. |
| `get_active_users()` | Queryset of active users. |
| `get_inactive_users()` | Queryset of inactive users. |
| `get_staff_users()` | Queryset of staff users. |
| `get_users_by_ids(user_ids)` | Queryset filtered to the given primary keys. |

### `users.managers.UserManager` / `UserQuerySet`

`User.objects` supports both Django's standard manager interface
(`create_user`, `create_superuser`) and chainable filters:

```python
User.objects.active().staff()
```

### `users.exceptions`

`UserModuleError` is the base class; all module exceptions inherit from it,
so callers can catch broadly (`except UserModuleError`) or narrowly
(`except EmailAlreadyExistsError`).

## Usage Examples

```python
from users.services import UserService
from users.selectors import get_user_by_email
from users.exceptions import EmailAlreadyExistsError

# Create a user
user = UserService.create_user(
    username="ada",
    email="ada@example.com",
    password="a-strong-password",
    first_name="Ada",
)

# Look a user up
user = get_user_by_email("ada@example.com")

# Deactivate / reactivate
UserService.deactivate_user(user_id=user.id)
UserService.activate_user(user_id=user.id)

# Update profile fields (email/password are intentionally ignored here)
UserService.update_profile(user_id=user.id, first_name="A.")

# Change email, with uniqueness enforced
try:
    UserService.change_email(user_id=user.id, new_email="taken@example.com")
except EmailAlreadyExistsError:
    ...
```

## Testing

The module ships with its own standalone test settings
(`users/tests/settings.py`) so the suite can run without a host project:

```bash
pip install pytest pytest-django factory-boy
pytest
```

Test coverage includes models, the custom manager/queryset, the service
layer, selectors, and validators, using `factory_boy` for test data.

## Module Layout

```
users/
├── admin.py        # Customized Django admin
├── apps.py         # AppConfig, wires up signals
├── exceptions.py   # Module exception hierarchy
├── forms.py        # Creation / change / profile-update forms
├── managers.py     # UserManager + UserQuerySet
├── models.py       # Custom User model
├── permissions.py  # Permission helper functions
├── selectors.py    # Read-only query helpers
├── services.py     # Business logic (UserService)
├── signals.py      # user_created / user_updated signals
├── urls.py         # Profile / deactivate routes
├── validators.py   # Username / email / avatar validators
├── views.py        # Thin views delegating to services
├── migrations/     # Database migrations
├── docs/           # Additional reference docs
├── tests/          # Test suite + factories
└── README.md
```
