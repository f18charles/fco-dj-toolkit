from typing import Any, List, Set
from django.conf import settings
from django.db.models import QuerySet
from django.db import IntegrityError

from permissions.models import Permission, Role, RolePermission, UserRole, UserPermission
from permissions.exceptions import (
    PermissionsModuleError,
    PermissionNotFoundError,
    RoleNotFoundError,
    RoleAlreadyAssignedError,
    PermissionAlreadyGrantedError,
    SystemRoleProtectedError,
    InvalidPermissionCodename,
    CircularRoleInheritanceError,
)
from permissions.signals import (
    role_created,
    role_assigned,
    role_revoked,
    permission_created,
    permission_granted_to_user,
    permission_revoked_from_user,
    permission_granted_to_role,
    permission_revoked_from_role,
    permission_checked,
)


class PermissionService:
    """
    Service class handling operations related to Permissions and direct assignments.
    """

    @staticmethod
    def create_permission(
        *, codename: str, name: str, module: str = "", description: str = ""
    ) -> Permission:
        """
        Create a Permission. Validates codename contains exactly one dot.
        Idempotent: if codename already exists, returns the existing record
        without raising.
        Raises: InvalidPermissionCodename if codename has no dot.
        """
        if not isinstance(codename, str) or codename.count(".") != 1:
            raise InvalidPermissionCodename(
                f"Permission codename '{codename}' must contain exactly one dot."
            )

        if not module:
            module = codename.split(".")[0]

        try:
            obj, created = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    "name": name,
                    "module": module,
                    "description": description,
                },
            )
            if created:
                permission_created.send(sender=PermissionService, permission=obj)
            return obj
        except Exception as e:
            raise PermissionsModuleError(f"Failed to create permission: {e}")

    @staticmethod
    def get_or_create_permission(codename: str) -> Permission:
        """Used internally by registry.sync(). Never raises for valid codenames."""
        if not isinstance(codename, str) or codename.count(".") != 1:
            raise InvalidPermissionCodename(
                f"Permission codename '{codename}' must contain exactly one dot."
            )

        try:
            module = codename.split(".")[0]
            name = codename.replace(".", " ").title()
            obj, created = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    "name": name,
                    "module": module,
                    "description": "",
                },
            )
            if created:
                permission_created.send(sender=PermissionService, permission=obj)
            return obj
        except Exception as e:
            raise PermissionsModuleError(f"Failed to get or create permission: {e}")

    @staticmethod
    def grant_permission_to_user(
        *, user: Any, codename: str, granted_by: Any = None, expires_at: Any = None
    ) -> UserPermission:
        """
        Grant a direct permission to a user.
        Raises: PermissionNotFoundError, PermissionAlreadyGrantedError.
        """
        try:
            permission = Permission.objects.get(codename=codename)
        except Permission.DoesNotExist:
            raise PermissionNotFoundError(f"Permission with codename '{codename}' not found.")

        try:
            obj = UserPermission.objects.create(
                user=user,
                permission=permission,
                granted_by=granted_by,
                expires_at=expires_at,
            )
            permission_granted_to_user.send(
                sender=PermissionService,
                user=user,
                permission=permission,
                granted_by=granted_by,
            )
            return obj
        except IntegrityError:
            raise PermissionAlreadyGrantedError(
                f"Permission '{codename}' is already granted to user."
            )
        except Exception as e:
            raise PermissionsModuleError(f"Failed to grant permission to user: {e}")

    @staticmethod
    def revoke_permission_from_user(*, user: Any, codename: str) -> None:
        """
        Revoke a direct permission from a user.
        Raises: PermissionNotFoundError, PermissionsModuleError if not currently granted.
        """
        try:
            permission = Permission.objects.get(codename=codename)
        except Permission.DoesNotExist:
            raise PermissionNotFoundError(f"Permission with codename '{codename}' not found.")

        try:
            user_permission = UserPermission.objects.get(user=user, permission=permission)
        except UserPermission.DoesNotExist:
            raise PermissionsModuleError(
                f"Permission '{codename}' is not directly granted to user."
            )

        try:
            user_permission.delete()
            permission_revoked_from_user.send(
                sender=PermissionService,
                user=user,
                permission=permission,
            )
        except Exception as e:
            raise PermissionsModuleError(f"Failed to revoke permission from user: {e}")

    @staticmethod
    def grant_permission_to_role(
        *, role_name: str, codename: str, granted_by: Any = None
    ) -> RolePermission:
        """
        Raises: RoleNotFoundError, PermissionNotFoundError, PermissionAlreadyGrantedError.
        """
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            raise RoleNotFoundError(f"Role '{role_name}' not found.")

        try:
            permission = Permission.objects.get(codename=codename)
        except Permission.DoesNotExist:
            raise PermissionNotFoundError(f"Permission with codename '{codename}' not found.")

        try:
            obj = RolePermission.objects.create(
                role=role,
                permission=permission,
                granted_by=granted_by,
            )
            permission_granted_to_role.send(
                sender=PermissionService,
                role=role,
                permission=permission,
                granted_by=granted_by,
            )
            return obj
        except IntegrityError:
            raise PermissionAlreadyGrantedError(
                f"Permission '{codename}' is already granted to role '{role_name}'."
            )
        except Exception as e:
            raise PermissionsModuleError(f"Failed to grant permission to role: {e}")

    @staticmethod
    def revoke_permission_from_role(*, role_name: str, codename: str) -> None:
        """
        Raises: RoleNotFoundError, PermissionNotFoundError.
        """
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            raise RoleNotFoundError(f"Role '{role_name}' not found.")

        try:
            permission = Permission.objects.get(codename=codename)
        except Permission.DoesNotExist:
            raise PermissionNotFoundError(f"Permission with codename '{codename}' not found.")

        try:
            role_permission = RolePermission.objects.get(role=role, permission=permission)
        except RolePermission.DoesNotExist:
            raise PermissionNotFoundError(
                f"Permission '{codename}' is not granted to role '{role_name}'."
            )

        try:
            role_permission.delete()
            permission_revoked_from_role.send(
                sender=PermissionService,
                role=role,
                permission=permission,
            )
        except Exception as e:
            raise PermissionsModuleError(f"Failed to revoke permission from role: {e}")

    @staticmethod
    def has_permission(*, user: Any, codename: str) -> bool:
        """
        Core runtime permission check. Resolution order:
        1. If settings.PERMISSIONS_SUPERUSER_BYPASS is True (default) and
           user.is_superuser is True: return True immediately.
        2. Check active direct UserPermission grants (respect expires_at).
        3. Check active UserRole assignments (respect expires_at), for each
           role check its permissions AND its parent role's permissions
           (single-level inheritance).
        4. Wildcard matching: if user has "posts.*" and codename is "posts.edit",
           return True.

        Cache the resolved permission set per-request on the user object
        (_permissions_cache attribute). Invalidated by post_save/post_delete
        signals on UserRole and UserPermission.

        Never raises. Returns False for any error condition.
        """
        try:
            is_anon = getattr(user, "is_anonymous", True)
            is_auth = getattr(user, "is_authenticated", False)
            print(f"DEBUG: user={user}, is_anon={is_anon}, is_auth={is_auth}, codename={codename}")
            if user is None or is_anon or not is_auth:
                print("DEBUG: Failed authentication/anonymity check")
                permission_checked.send(
                    sender=PermissionService, user=user, codename=codename, result=False
                )
                return False

            # 1. Superuser bypass
            bypass = getattr(settings, "PERMISSIONS_SUPERUSER_BYPASS", True)
            if bypass and getattr(user, "is_superuser", False):
                print("DEBUG: Superuser bypass applied")
                permission_checked.send(
                    sender=PermissionService, user=user, codename=codename, result=True
                )
                return True

            # 2. Check/populate cache
            if not hasattr(user, "_permissions_cache"):
                # Active direct UserPermission grants
                direct_perms = list(
                    UserPermission.objects.filter(user=user)
                    .active()
                    .values_list("permission__codename", flat=True)
                )

                # Active UserRole assignments (and their parent roles)
                active_user_roles = (
                    UserRole.objects.filter(user=user)
                    .active()
                    .select_related("role__parent")
                )

                role_ids = []
                parent_ids = []
                for ur in active_user_roles:
                    role_ids.append(ur.role_id)
                    if ur.role.parent_id:
                        parent_ids.append(ur.role.parent_id)

                all_role_ids = set(role_ids) | set(parent_ids)

                role_perms = list(
                    RolePermission.objects.filter(role_id__in=all_role_ids)
                    .values_list("permission__codename", flat=True)
                )

                user._permissions_cache = set(direct_perms) | set(role_perms)
                print(f"DEBUG: populated cache for {user}: {user._permissions_cache}")

            # 3. Check exact match
            if codename in user._permissions_cache:
                print("DEBUG: Exact match found in cache")
                permission_checked.send(
                    sender=PermissionService, user=user, codename=codename, result=True
                )
                return True

            # 4. Wildcard matching
            if "." in codename:
                module, _ = codename.split(".", 1)
                wildcard_codename = f"{module}.*"
                if wildcard_codename in user._permissions_cache:
                    print(f"DEBUG: Wildcard match found in cache: {wildcard_codename}")
                    permission_checked.send(
                        sender=PermissionService, user=user, codename=codename, result=True
                    )
                    return True

            print("DEBUG: No permission match found")
            permission_checked.send(
                sender=PermissionService, user=user, codename=codename, result=False
            )
            return False
        except Exception as e:
            print(f"DEBUG: Exception in has_permission: {e}")
            # Never raises, return False on error
            return False

    @staticmethod
    def has_any_permission(*, user: Any, codenames: List[str]) -> bool:
        """Return True if user has at least one of the given codenames."""
        for cn in codenames:
            if PermissionService.has_permission(user=user, codename=cn):
                return True
        return False

    @staticmethod
    def has_all_permissions(*, user: Any, codenames: List[str]) -> bool:
        """Return True if user has every one of the given codenames."""
        for cn in codenames:
            if not PermissionService.has_permission(user=user, codename=cn):
                return False
        return True


class RoleService:
    """
    Service class handling operations related to Roles and assignments.
    """

    @staticmethod
    def create_role(
        *,
        name: str,
        description: str = "",
        parent_name: str | None = None,
        is_system_role: bool = False,
    ) -> Role:
        """
        Create a role. If parent_name is given, resolve the parent role first.
        Raises: RoleNotFoundError (for parent), CircularRoleInheritanceError
        if name == parent_name.
        """
        if parent_name == name and parent_name is not None:
            raise CircularRoleInheritanceError(
                f"Role '{name}' cannot be its own parent."
            )

        try:
            parent = None
            if parent_name:
                try:
                    parent = Role.objects.get(name=parent_name)
                except Role.DoesNotExist:
                    raise RoleNotFoundError(f"Parent role '{parent_name}' not found.")

            try:
                obj = Role.objects.create(
                    name=name,
                    description=description,
                    parent=parent,
                    is_system_role=is_system_role,
                )
                role_created.send(sender=RoleService, role=obj)
                return obj
            except IntegrityError:
                raise PermissionsModuleError(f"Role with name '{name}' already exists.")
        except PermissionsModuleError:
            raise
        except Exception as e:
            raise PermissionsModuleError(f"Failed to create role: {e}")

    @staticmethod
    def assign_role(
        *, user: Any, role_name: str, granted_by: Any = None, expires_at: Any = None
    ) -> UserRole:
        """
        Assign a role to a user.
        Raises: RoleNotFoundError, RoleAlreadyAssignedError.
        Invalidates the user's permission cache after assignment.
        Sends role_assigned signal.
        """
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            raise RoleNotFoundError(f"Role '{role_name}' not found.")

        try:
            obj = UserRole.objects.create(
                user=user,
                role=role,
                granted_by=granted_by,
                expires_at=expires_at,
            )
            # Invalidate cache
            if hasattr(user, "_permissions_cache"):
                del user._permissions_cache

            role_assigned.send(
                sender=RoleService,
                user=user,
                role=role,
                granted_by=granted_by,
            )
            return obj
        except IntegrityError:
            raise RoleAlreadyAssignedError(
                f"Role '{role_name}' is already assigned to user."
            )
        except Exception as e:
            raise PermissionsModuleError(f"Failed to assign role: {e}")

    @staticmethod
    def revoke_role(*, user: Any, role_name: str) -> None:
        """
        Raises: RoleNotFoundError, PermissionsModuleError if role not currently assigned.
        Invalidates cache. Sends role_revoked signal.
        """
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            raise RoleNotFoundError(f"Role '{role_name}' not found.")

        try:
            user_role = UserRole.objects.get(user=user, role=role)
        except UserRole.DoesNotExist:
            raise PermissionsModuleError(
                f"Role '{role_name}' is not assigned to user."
            )

        try:
            user_role.delete()
            # Invalidate cache
            if hasattr(user, "_permissions_cache"):
                del user._permissions_cache

            role_revoked.send(sender=RoleService, user=user, role=role)
        except Exception as e:
            raise PermissionsModuleError(f"Failed to revoke role: {e}")

    @staticmethod
    def get_user_roles(*, user: Any) -> QuerySet:
        """Return active UserRole assignments for user (respects expires_at)."""
        try:
            return UserRole.objects.filter(user=user).active()
        except Exception as e:
            raise PermissionsModuleError(f"Failed to get user roles: {e}")

    @staticmethod
    def clone_role(*, source_role_name: str, new_name: str) -> Role:
        """
        Create a new role copying all permissions from source_role.
        The clone has no parent (even if source does)  caller sets parent
        explicitly via create_role if needed.
        Raises: RoleNotFoundError if source does not exist.
        """
        try:
            source_role = Role.objects.get(name=source_role_name)
        except Role.DoesNotExist:
            raise RoleNotFoundError(f"Source role '{source_role_name}' not found.")

        try:
            new_role = Role.objects.create(
                name=new_name,
                description=f"Clone of {source_role_name}",
            )
            role_created.send(sender=RoleService, role=new_role)

            source_perms = RolePermission.objects.filter(role=source_role)
            role_permissions_to_create = []
            for sp in source_perms:
                role_permissions_to_create.append(
                    RolePermission(
                        role=new_role,
                        permission=sp.permission,
                        granted_by=sp.granted_by,
                    )
                )

            if role_permissions_to_create:
                RolePermission.objects.bulk_create(role_permissions_to_create)

            return new_role
        except Exception as e:
            raise PermissionsModuleError(f"Failed to clone role: {e}")

    @staticmethod
    def delete_role(*, role_name: str) -> None:
        """
        Raises: RoleNotFoundError, SystemRoleProtectedError if is_system_role=True.
        """
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            raise RoleNotFoundError(f"Role '{role_name}' not found.")

        if role.is_system_role:
            raise SystemRoleProtectedError(
                f"Role '{role_name}' is a system role and cannot be deleted."
            )

        try:
            role.delete()
        except Exception as e:
            raise PermissionsModuleError(f"Failed to delete role: {e}")
