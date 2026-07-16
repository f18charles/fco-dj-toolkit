from django.apps import AppConfig


class PermissionsConfig(AppConfig):
    name = "permissions"
    verbose_name = "Permissions"

    def ready(self):
        from permissions import signals  # noqa: F401  register signal handlers
        from permissions.registry import registry
        registry.sync()
