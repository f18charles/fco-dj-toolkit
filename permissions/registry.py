from typing import Dict, List, Any
from django.core.exceptions import ValidationError


class PermissionRegistry:
    """
    In-memory registry of permissions defined across modules.
    Provides utility to synchronize in-memory declarations to database.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        codename: str,
        name: str,
        *,
        module: str = "",
        description: str = "",
    ) -> None:
        """
        Declare a permission. Called in other modules' AppConfig.ready().
        Stores declarations in memory only; does not touch the database.
        Safe to call multiple times with the same codename (idempotent).
        """
        # Simple validation check on codename format (exactly one dot)
        if not isinstance(codename, str) or codename.count(".") != 1:
            raise ValidationError(
                "Permission codename must contain exactly one dot (e.g., 'module.action')."
            )

        self._registry[codename] = {
            "name": name,
            "module": module,
            "description": description,
        }

    def sync(self) -> List[Any]:
        """
        Write all registered declarations to the database.
        Returns the list of Permission objects that were created (newly added).
        """
        # Import models locally to avoid import issues before ready()
        from permissions.models import Permission

        created_permissions = []
        for codename, info in self._registry.items():
            # Extract module from codename if not explicitly provided
            module = info["module"] or codename.split(".")[0]
            obj, created = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    "name": info["name"],
                    "module": module,
                    "description": info["description"],
                },
            )
            if created:
                created_permissions.append(obj)
        return created_permissions

    def get_registered(self) -> Dict[str, Dict[str, Any]]:
        """Return all in-memory declarations."""
        return self._registry

    def is_registered(self, codename: str) -> bool:
        """Return True if codename has been declared via register()."""
        return codename in self._registry


# Module-level singleton
registry = PermissionRegistry()
