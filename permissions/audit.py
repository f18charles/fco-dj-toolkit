"""
permissions/audit.py
====================

Example signal receivers for connecting the permissions module to a future
`audit_logs` module. None of these receivers are active by default — they are
documented patterns for module authors to adapt.

To activate any of these, copy the receiver into your audit_logs app's
signals.py and connect it appropriately.
"""

# Example: log every role assignment
# @receiver(role_assigned)
# def log_role_assigned(sender, user, role, granted_by, **kwargs):
#     from audit_logs.services import AuditLogService
#     AuditLogService.log(
#         actor=granted_by,
#         action="permissions.role_assigned",
#         target=user,
#         metadata={"role": role.name},
#     )

# Example: log every role revocation
# @receiver(role_revoked)
# def log_role_revoked(sender, user, role, **kwargs):
#     from audit_logs.services import AuditLogService
#     AuditLogService.log(
#         action="permissions.role_revoked",
#         target=user,
#         metadata={"role": role.name},
#     )

# Example: log every direct permission grant to a user
# @receiver(permission_granted_to_user)
# def log_permission_granted_to_user(sender, user, permission, granted_by, **kwargs):
#     from audit_logs.services import AuditLogService
#     AuditLogService.log(
#         actor=granted_by,
#         action="permissions.permission_granted_to_user",
#         target=user,
#         metadata={"permission": permission.codename},
#     )

# Example: log every object permission grant
# @receiver(object_permission_granted)
# def log_object_permission_granted(sender, user, permission, obj, granted_by, **kwargs):
#     from audit_logs.services import AuditLogService
#     AuditLogService.log(
#         actor=granted_by,
#         action="permissions.object_permission_granted",
#         target=user,
#         metadata={"permission": permission.codename, "object": str(obj)},
#     )

# Example: log every scoped role assignment
# @receiver(scoped_role_assigned)
# def log_scoped_role_assigned(sender, user, role, scope, granted_by, **kwargs):
#     from audit_logs.services import AuditLogService
#     AuditLogService.log(
#         actor=granted_by,
#         action="permissions.scoped_role_assigned",
#         target=user,
#         metadata={"role": role.name, "scope": str(scope)},
#     )
