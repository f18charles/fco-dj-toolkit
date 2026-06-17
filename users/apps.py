from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    Application configuration for the `users` module.

    Wires up the signal handlers defined in `users.signals` when the
    app registry is fully populated.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    verbose_name = "Users"

    def ready(self) -> None:
        # Imported for side effects: registers the post_save receiver
        # that dispatches the module's semantic user_created /
        # user_updated signals. See users/signals.py.
        from users import signals  # noqa: F401
