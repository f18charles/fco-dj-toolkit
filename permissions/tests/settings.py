INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "common",
    "users",
    "permissions",
]
AUTH_USER_MODEL = "users.User"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
USE_TZ = True
SECRET_KEY = "test-only"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
PERMISSIONS_SUPERUSER_BYPASS = True
ROOT_URLCONF = "permissions.tests.urls"
LOGIN_URL = "/login/"

