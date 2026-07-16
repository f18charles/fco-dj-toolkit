from django.dispatch import Signal

# Signal sent after a new role is created.
# Arguments: role
role_created = Signal()
# Example receiver for audit_logs:
# @receiver(role_created)
# def log_role_created(sender, role, **kwargs):
#     AuditLogService.log_event(
#         action="role_created",
#         target=f"role:{role.name}",
#     )

# Signal sent after a role is assigned to a user.
# Arguments: user, role, granted_by
role_assigned = Signal()
# Example receiver for audit_logs:
# @receiver(role_assigned)
# def log_role_assigned(sender, user, role, granted_by, **kwargs):
#     AuditLogService.log_event(
#         action="role_assigned",
#         target=f"user:{user.pk}",
#         actor=granted_by,
#         context={"role": role.name},
#     )

# Signal sent after a role is revoked from a user.
# Arguments: user, role
role_revoked = Signal()
# Example receiver for audit_logs:
# @receiver(role_revoked)
# def log_role_revoked(sender, user, role, **kwargs):
#     AuditLogService.log_event(
#         action="role_revoked",
#         target=f"user:{user.pk}",
#         context={"role": role.name},
#     )

# Signal sent after a new permission is created.
# Arguments: permission
permission_created = Signal()
# Example receiver for audit_logs:
# @receiver(permission_created)
# def log_permission_created(sender, permission, **kwargs):
#     AuditLogService.log_event(
#         action="permission_created",
#         target=f"permission:{permission.codename}",
#     )

# Signal sent after a direct permission is granted to a user.
# Arguments: user, permission, granted_by
permission_granted_to_user = Signal()
# Example receiver for audit_logs:
# @receiver(permission_granted_to_user)
# def log_permission_granted_to_user(sender, user, permission, granted_by, **kwargs):
#     AuditLogService.log_event(
#         action="permission_granted_to_user",
#         target=f"user:{user.pk}",
#         actor=granted_by,
#         context={"permission": permission.codename},
#     )

# Signal sent after a direct permission is revoked from a user.
# Arguments: user, permission
permission_revoked_from_user = Signal()
# Example receiver for audit_logs:
# @receiver(permission_revoked_from_user)
# def log_permission_revoked_from_user(sender, user, permission, **kwargs):
#     AuditLogService.log_event(
#         action="permission_revoked_from_user",
#         target=f"user:{user.pk}",
#         context={"permission": permission.codename},
#     )

# Signal sent after a permission is granted to a role.
# Arguments: role, permission, granted_by
permission_granted_to_role = Signal()
# Example receiver for audit_logs:
# @receiver(permission_granted_to_role)
# def log_permission_granted_to_role(sender, role, permission, granted_by, **kwargs):
#     AuditLogService.log_event(
#         action="permission_granted_to_role",
#         target=f"role:{role.name}",
#         actor=granted_by,
#         context={"permission": permission.codename},
#     )

# Signal sent after a permission is revoked from a role.
# Arguments: role, permission
permission_revoked_from_role = Signal()
# Example receiver for audit_logs:
# @receiver(permission_revoked_from_role)
# def log_permission_revoked_from_role(sender, role, permission, **kwargs):
#     AuditLogService.log_event(
#         action="permission_revoked_from_role",
#         target=f"role:{role.name}",
#         context={"permission": permission.codename},
#     )

# Signal sent on every permission check (runtime).
# Arguments: user, codename, result (bool)
permission_checked = Signal()
# Example receiver for audit_logs / PermissionAuditMiddleware:
# @receiver(permission_checked)
# def log_permission_checked(sender, user, codename, result, **kwargs):
#     logger.debug(f"Permission check: user={user}, permission={codename}, allowed={result}")
