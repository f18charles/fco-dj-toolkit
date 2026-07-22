from typing import Any, List, Set
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.db import IntegrityError

from permissions.models import (
    Permission,
    Role,
    RolePermission,
    UserRole,
    UserPermission,
    ObjectPermission,
    ScopedUserRole,
    PermissionGroup,
)
from permissions.exceptions import (
    PermissionsModuleError,
    PermissionNotFoundError,
    RoleNotFoundError,
    RoleAlreadyAssignedError,
    PermissionAlreadyGrantedError,
    SystemRoleProtectedError,
    InvalidPermissionCodename,
    CircularRoleInheritanceError,
    ObjectPermissionNotFoundError,
    ObjectPermissionAlreadyGrantedError,
    ScopedRoleAlreadyAssignedError,
    ScopeRequiredError,
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
    object_permission_granted,
    object_permission_revoked,
    object_permission_checked,
    scoped_role_assigned,
    scoped_role_revoked,
)
from permissions.cache import (
    get_user_permissions_from_cache,
    set_user_permissions_cache,
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
            if hasattr(user, "_permissions_cache"):
                del user._permissions_cache

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
            user_perm = UserPermission.objects.get(user=user, permission=permission)
        except UserPermission.DoesNotExist:
            raise PermissionsModuleError(
                f"Permission '{codename}' is not directly granted to user."
            )

        try:
            user_perm.delete()
            if hasattr(user, "_permissions_cache"):
                del user._permissions_cache

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
    def has_permission(*, user: Any, codename: str, obj: Any = None, scope: Any = None) -> bool:
        """
        Core runtime permission check. Resolution order:
        1. Superuser bypass.
        2. Object-level permission check (if obj is provided).
        3. Scoped role assignment check (if scope is provided).
        4. Global check (direct grants -> roles -> inherited -> wildcards).
        """
        try:
            is_anon = getattr(user, "is_anonymous", True)
            is_auth = getattr(user, "is_authenticated", False)
            if user is None or is_anon or not is_auth:
                permission_checked.send(
                    sender=PermissionService, user=user, codename=codename, result=False
                )
                return False

            # 1. Superuser bypass
            bypass = getattr(settings, "PERMISSIONS_SUPERUSER_BYPASS", True)
            if bypass and getattr(user, "is_superuser", False):
                permission_checked.send(
                    sender=PermissionService, user=user, codename=codename, result=True
                )
                return True

            # 2. ObjectPermission check (if obj provided)
            if obj is not None:
                if ObjectPermissionService.has_object_permission(user=user, codename=codename, obj=obj):
                    permission_checked.send(
                        sender=PermissionService, user=user, codename=codename, result=True
                    )
                    return True

            # 3. ScopedUserRole check (if scope provided)
            if scope is not None:
                scoped_perms = ScopedPermissionService.get_all_permissions_for_user_in_scope(user=user, scope=scope)
                if codename in scoped_perms:
                    permission_checked.send(
                        sender=PermissionService, user=user, codename=codename, result=True
                    )
                    return True
                if "." in codename:
                    mod, _ = codename.split(".", 1)
                    if f"{mod}.*" in scoped_perms:
                        permission_checked.send(
                            sender=PermissionService, user=user, codename=codename, result=True
                        )
                        return True
                permission_checked.send(
                    sender=PermissionService, user=user, codename=codename, result=False
                )
                return False

            # 4. Global check
            cached_perms = get_user_permissions_from_cache(user)
            if cached_perms is not None:
                user._permissions_cache = cached_perms

            if not hasattr(user, "_permissions_cache"):
                from permissions.selectors import get_all_permissions_for_user
                user._permissions_cache = get_all_permissions_for_user(user)
                set_user_permissions_cache(user, user._permissions_cache)

            if codename in user._permissions_cache:
                permission_checked.send(
                    sender=PermissionService, user=user, codename=codename, result=True
                )
                return True

            if "." in codename:
                module, _ = codename.split(".", 1)
                wildcard_codename = f"{module}.*"
                if wildcard_codename in user._permissions_cache:
                    permission_checked.send(
                        sender=PermissionService, user=user, codename=codename, result=True
                    )
                    return True

            permission_checked.send(
                sender=PermissionService, user=user, codename=codename, result=False
            )
            return False
        except Exception:
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


class ObjectPermissionService:
    """
    Service class handling object-level permissions.
    """

    @staticmethod
    def grant(
        *, user: Any, codename: str, obj: Any, granted_by: Any = None, expires_at: Any = None
    ) -> ObjectPermission:
        try:
            permission = Permission.objects.get(codename=codename)
        except Permission.DoesNotExist:
            raise PermissionNotFoundError(f"Permission with codename '{codename}' not found.")

        ct = ContentType.objects.get_for_model(obj)
        object_id = str(obj.pk)

        try:
            op, created = ObjectPermission.objects.get_or_create(
                user=user,
                permission=permission,
                content_type=ct,
                object_id=object_id,
                defaults={
                    "granted_by": granted_by,
                    "expires_at": expires_at,
                },
            )
            if not created:
                raise ObjectPermissionAlreadyGrantedError(
                    f"Object permission '{codename}' already granted to user on object."
                )
            object_permission_granted.send(
                sender=ObjectPermissionService,
                user=user,
                permission=permission,
                obj=obj,
                granted_by=granted_by,
            )
            return op
        except ObjectPermissionAlreadyGrantedError:
            raise
        except Exception as e:
            raise PermissionsModuleError(f"Failed to grant object permission: {e}")

    @staticmethod
    def revoke(*, user: Any, codename: str, obj: Any) -> None:
        try:
            permission = Permission.objects.get(codename=codename)
        except Permission.DoesNotExist:
            raise PermissionNotFoundError(f"Permission with codename '{codename}' not found.")

        ct = ContentType.objects.get_for_model(obj)
        object_id = str(obj.pk)

        try:
            op = ObjectPermission.objects.get(
                user=user,
                permission=permission,
                content_type=ct,
                object_id=object_id,
            )
        except ObjectPermission.DoesNotExist:
            raise ObjectPermissionNotFoundError(
                f"Object permission '{codename}' is not granted to user on object."
            )

        try:
            op.delete()
            object_permission_revoked.send(
                sender=ObjectPermissionService,
                user=user,
                permission=permission,
                obj=obj,
            )
        except Exception as e:
            raise PermissionsModuleError(f"Failed to revoke object permission: {e}")

    @staticmethod
    def has_object_permission(*, user: Any, codename: str, obj: Any) -> bool:
        """
        Check if user has `codename` on the specific object `obj`.
        Does NOT fall through to global permissions.
        Never raises. Returns False for any error condition.
        """
        try:
            is_anon = getattr(user, "is_anonymous", True)
            is_auth = getattr(user, "is_authenticated", False)
            if user is None or is_anon or not is_auth:
                object_permission_checked.send(
                    sender=ObjectPermissionService, user=user, codename=codename, obj=obj, result=False
                )
                return False

            ct = ContentType.objects.get_for_model(obj)
            object_id = str(obj.pk)
            exists = ObjectPermission.objects.filter(
                user=user,
                permission__codename=codename,
                content_type=ct,
                object_id=object_id,
            ).active().exists()

            object_permission_checked.send(
                sender=ObjectPermissionService, user=user, codename=codename, obj=obj, result=exists
            )
            return exists
        except Exception:
            return False

    @staticmethod
    def get_users_with_permission_on_object(codename: str, obj: Any) -> QuerySet:
        """Return all users who have `codename` on object `obj` (active grants only)."""
        try:
            ct = ContentType.objects.get_for_model(obj)
            object_id = str(obj.pk)
            user_ids = ObjectPermission.objects.filter(
                permission__codename=codename,
                content_type=ct,
                object_id=object_id,
            ).active().values_list("user_id", flat=True)
            from django.contrib.auth import get_user_model
            UserModel = get_user_model()
            return UserModel.objects.filter(pk__in=list(user_ids))
        except Exception as e:
            raise PermissionsModuleError(f"Failed to get users with permission on object: {e}")

    @staticmethod
    def get_objects_user_can_access(user: Any, codename: str, model_class: Any) -> QuerySet:
        """
        Return a queryset of `model_class` instances that `user` has `codename` permission on via ObjectPermission.
        Does NOT include objects accessed via global permissions.
        """
        try:
            ct = ContentType.objects.get_for_model(model_class)
            object_ids = ObjectPermission.objects.filter(
                user=user,
                permission__codename=codename,
                content_type=ct,
            ).active().values_list("object_id", flat=True)
            return model_class.objects.filter(pk__in=list(object_ids))
        except Exception as e:
            raise PermissionsModuleError(f"Failed to get objects user can access: {e}")


class ScopedPermissionService:
    """
    Service class handling scoped role assignments and permissions.
    """

    @staticmethod
    def assign_scoped_role(
        *, user: Any, role_name: str, scope: Any, granted_by: Any = None, expires_at: Any = None
    ) -> ScopedUserRole:
        if scope is None:
            raise ScopeRequiredError("Scope object is required for scoped role assignment.")
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            raise RoleNotFoundError(f"Role '{role_name}' not found.")

        ct = ContentType.objects.get_for_model(scope)
        object_id = str(scope.pk)

        try:
            sur, created = ScopedUserRole.objects.get_or_create(
                user=user,
                role=role,
                content_type=ct,
                object_id=object_id,
                defaults={
                    "granted_by": granted_by,
                    "expires_at": expires_at,
                },
            )
            if not created:
                raise ScopedRoleAlreadyAssignedError(
                    f"Role '{role_name}' is already assigned to user within scope."
                )

            if hasattr(user, "_permissions_cache"):
                del user._permissions_cache

            scoped_role_assigned.send(
                sender=ScopedPermissionService,
                user=user,
                role=role,
                scope=scope,
                granted_by=granted_by,
            )
            return sur
        except ScopedRoleAlreadyAssignedError:
            raise
        except Exception as e:
            raise PermissionsModuleError(f"Failed to assign scoped role: {e}")

    @staticmethod
    def revoke_scoped_role(*, user: Any, role_name: str, scope: Any) -> None:
        if scope is None:
            raise ScopeRequiredError("Scope object is required for scoped role revocation.")
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            raise RoleNotFoundError(f"Role '{role_name}' not found.")

        ct = ContentType.objects.get_for_model(scope)
        object_id = str(scope.pk)

        try:
            sur = ScopedUserRole.objects.get(
                user=user,
                role=role,
                content_type=ct,
                object_id=object_id,
            )
        except ScopedUserRole.DoesNotExist:
            raise PermissionsModuleError(
                f"Scoped role '{role_name}' is not assigned to user within scope."
            )

        try:
            sur.delete()
            if hasattr(user, "_permissions_cache"):
                del user._permissions_cache

            scoped_role_revoked.send(
                sender=ScopedPermissionService,
                user=user,
                role=role,
                scope=scope,
            )
        except Exception as e:
            raise PermissionsModuleError(f"Failed to revoke scoped role: {e}")

    @staticmethod
    def get_scoped_roles_for_user(*, user: Any, scope: Any) -> QuerySet[ScopedUserRole]:
        try:
            return ScopedUserRole.objects.filter(user=user).for_scope(scope).active()
        except Exception as e:
            raise PermissionsModuleError(f"Failed to get scoped roles for user: {e}")

    @staticmethod
    def get_all_permissions_for_user_in_scope(*, user: Any, scope: Any) -> Set[str]:
        try:
            active_scoped_roles = (
                ScopedUserRole.objects.filter(user=user)
                .for_scope(scope)
                .active()
                .select_related("role__parent")
            )
            role_ids = []
            parent_ids = []
            for sur in active_scoped_roles:
                role_ids.append(sur.role_id)
                if sur.role.parent_id:
                    parent_ids.append(sur.role.parent_id)

            all_role_ids = set(role_ids) | set(parent_ids)
            role_perms = RolePermission.objects.filter(
                role_id__in=all_role_ids
            ).values_list("permission__codename", flat=True)
            return set(role_perms)
        except Exception as e:
            raise PermissionsModuleError(f"Failed to resolve permissions in scope: {e}")


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
