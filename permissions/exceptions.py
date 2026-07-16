from common.exceptions import FcoKitException


class PermissionsModuleError(FcoKitException):
    """
    Base exception class for all errors in the permissions module.
    """
    def __init__(self, message: str, code: str = "permissions_error"):
        super().__init__(message, code)


class PermissionNotFoundError(PermissionsModuleError):
    """
    Raised when a requested permission is not found.
    """
    def __init__(self, message: str = "Permission not found.", code: str = "permission_not_found"):
        super().__init__(message, code)


class RoleNotFoundError(PermissionsModuleError):
    """
    Raised when a requested role is not found.
    """
    def __init__(self, message: str = "Role not found.", code: str = "role_not_found"):
        super().__init__(message, code)


class RoleAlreadyAssignedError(PermissionsModuleError):
    """
    Raised when a role is already assigned to a user.
    """
    def __init__(self, message: str = "Role already assigned to user.", code: str = "role_already_assigned"):
        super().__init__(message, code)


class PermissionAlreadyGrantedError(PermissionsModuleError):
    """
    Raised when a permission is already granted to a user or role.
    """
    def __init__(self, message: str = "Permission already granted.", code: str = "permission_already_granted"):
        super().__init__(message, code)


class SystemRoleProtectedError(PermissionsModuleError):
    """
    Raised when attempting to delete or modify a system-protected role.
    """
    def __init__(self, message: str = "System roles are protected and cannot be deleted.", code: str = "system_role_protected"):
        super().__init__(message, code)


class InvalidPermissionCodename(PermissionsModuleError):
    """
    Raised when a permission codename is invalid (does not contain exactly one dot).
    """
    def __init__(self, message: str = "Permission codename must contain exactly one dot.", code: str = "invalid_codename"):
        super().__init__(message, code)


class CircularRoleInheritanceError(PermissionsModuleError):
    """
    Raised when a circular dependency is detected in role inheritance.
    """
    def __init__(self, message: str = "Circular role inheritance detected.", code: str = "circular_role_inheritance"):
        super().__init__(message, code)
