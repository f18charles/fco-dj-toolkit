# Configuration

## Required settings

```python
AUTH_USER_MODEL = "users.User"
```

This must be set **before** the first `migrate` is run in the
consuming project — Django does not support swapping the user model
after the fact.

## Optional settings

### Media storage (avatars)

`User.avatar` is a standard `ImageField`, so the usual project-level
settings apply:

```python
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"
```

Avatar uploads are validated by `users.validators.validate_avatar_image`,
which enforces:

- Allowed content types: `image/jpeg`, `image/png`, `image/webp`.
- Max size: 5MB (`MAX_AVATAR_SIZE_MB` in `validators.py`).

To change these limits, override the module-level constants in
`validators.py` or fork the validator.

### URL inclusion

```python
# project urls.py
from django.urls import include, path

urlpatterns = [
    path("users/", include("users.urls")),
]
```

Exposes three routes under the `users` namespace: `users:profile`,
`users:profile-edit`, and `users:deactivate`.

### Admin

No extra configuration needed — registering `users` in `INSTALLED_APPS`
along with `django.contrib.admin` is sufficient. The module's
`UserAdmin` replaces Django's default registration for the user model.

### Templates

`users/templates/users/` ships minimal templates for the three views
in `views.py` (`profile_detail.html`, `profile_update.html`,
`error.html`). They all `{% extends "base.html" %}` and fill a
`content` block, so the consuming project should provide its own
`base.html` with that block — these are deliberately unstyled
scaffolding, not a finished UI.

To extend behavior on user creation/update without modifying this
module, connect to its semantic signals from your own app:

```python
from django.dispatch import receiver
from users.signals import user_created

@receiver(user_created)
def on_user_created(sender, user, **kwargs):
    ...
```
