"""
Minimal Django settings used only to run this module's test suite in
isolation (via pytest-django). Consuming projects should NOT import
this file; it exists purely so `users` can be tested as a standalone,
installable app.
"""
SECRET_KEY = "test-secret-key-not-for-production"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "users",
]

AUTH_USER_MODEL = "users.User"

USE_TZ = True

MEDIA_ROOT = "/tmp/fco-dj-kit-users-test-media"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",  # fast hashing for tests only
]
