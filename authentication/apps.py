from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuthenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "authentication"
    verbose_name = _("Authentication")

    def ready(self) -> None:
        # Import core signals only, avoiding import-time dependencies on auth_methods
        import authentication.core.signals  # noqa
