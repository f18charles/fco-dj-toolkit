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

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
    "permissions": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}

PERMISSIONS_CACHE_BACKEND = "permissions"
PERMISSIONS_CACHE_TTL = 60

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
            ],
            "libraries": {
                "permissions_tags": "permissions.templatetags.permissions_tags",
            },
        },
    }
]


