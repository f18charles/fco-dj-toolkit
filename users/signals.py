"""
Signals for the users module.

Two semantic signals are exposed: `user_created` and `user_updated`.
Other modules (notifications, audit_logs, activity_feed, etc.) should
import and listen to these rather than depending on `post_save` +
`sender=User` directly, which keeps them decoupled from this module's
internal model.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import Signal, receiver

User = get_user_model()

# Sent whenever a new user is created.
# Keyword args sent: user
user_created = Signal()

# Sent whenever an existing user is saved (but not on creation).
# Keyword args sent: user, updated_fields (may be None)
user_updated = Signal()


@receiver(post_save, sender=User)
def _dispatch_user_lifecycle_signals(sender, instance, created, **kwargs) -> None:
    """
    Translate Django's generic `post_save` into this module's semantic
    `user_created` / `user_updated` signals.
    """
    if created:
        user_created.send(sender=sender, user=instance)
    else:
        user_updated.send(sender=sender, user=instance, updated_fields=None)


# ---------------------------------------------------------------------------
# Examples of future extensibility (intentionally left as comments).
# Other planned modules can hook into these signals without any changes
# to the users module itself:
#
# @receiver(user_created)
# def send_welcome_email(sender, user, **kwargs):
#     from notifications.services import NotificationService
#     NotificationService.send_welcome_email(user)
#
# @receiver(user_created)
# def log_user_created(sender, user, **kwargs):
#     from audit_logs.services import AuditLogService
#     AuditLogService.log_event(actor=user, action="user.created")
#
# @receiver(user_updated)
# def log_user_updated(sender, user, updated_fields, **kwargs):
#     from audit_logs.services import AuditLogService
#     AuditLogService.log_event(actor=user, action="user.updated")
# ---------------------------------------------------------------------------
