from __future__ import annotations

from datetime import timedelta
from typing import Any, Optional

from django.http import HttpRequest
from django.utils import timezone

from authentication.core.models import LoginAttempt


class LoginThrottle:
    """
    Handles brute-force protection logic by tracking failed login attempts.
    """

    def __init__(
        self,
        max_failed_attempts: int = 5,
        window_minutes: int = 15,
        lockout_minutes: int = 15,
    ):
        self.max_failed_attempts = max_failed_attempts
        self.window_minutes = window_minutes
        self.lockout_minutes = lockout_minutes

    def failed_attempt_count(self, identifier: str) -> int:
        """
        Count the number of failed attempts within the window_minutes,
        restricted to attempts after the most recent successful login if any.
        """
        now = timezone.now()
        window_start = now - timedelta(minutes=self.window_minutes)

        qs = LoginAttempt.objects.for_identifier(identifier)

        # Check for any successful login within the window or generally
        # to reset the count of consecutive failed attempts.
        last_success = qs.successful().filter(created_at__gte=window_start).first()

        failed_qs = qs.failed().filter(created_at__gte=window_start)
        if last_success:
            failed_qs = failed_qs.filter(created_at__gt=last_success.created_at)

        return failed_qs.count()

    def is_locked_out(self, identifier: str) -> bool:
        """
        Check if the identifier is currently locked out.
        """
        if self.failed_attempt_count(identifier) < self.max_failed_attempts:
            return False

        # Lockout is active if the most recent failed attempt was within lockout_minutes
        last_failed = LoginAttempt.objects.for_identifier(identifier).failed().first()
        if not last_failed:
            return False

        lockout_expiry = last_failed.created_at + timedelta(minutes=self.lockout_minutes)
        return timezone.now() < lockout_expiry

    def seconds_until_unlock(self, identifier: str) -> int:
        """
        Calculate seconds remaining until the lockout is lifted.
        """
        if not self.is_locked_out(identifier):
            return 0

        last_failed = LoginAttempt.objects.for_identifier(identifier).failed().first()
        if not last_failed:
            return 0

        lockout_expiry = last_failed.created_at + timedelta(minutes=self.lockout_minutes)
        remaining = (lockout_expiry - timezone.now()).total_seconds()
        return max(0, int(remaining))

    def record_attempt(
        self,
        identifier: str,
        was_successful: bool,
        request: Optional[HttpRequest] = None,
        user: Any = None,
        failure_reason: str = "",
    ) -> LoginAttempt:
        """
        Create and save a LoginAttempt entry.
        """
        ip_address = None
        user_agent = ""

        if request is not None:
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]
            # Retrieve client IP, resolving standard headers if present
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(",")[0].strip()
            else:
                ip_address = request.META.get("REMOTE_ADDR")

        return LoginAttempt.objects.create(
            user=user,
            identifier=identifier,
            ip_address=ip_address,
            user_agent=user_agent,
            was_successful=was_successful,
            failure_reason=failure_reason,
        )


# Module-level default instance
default_login_throttle = LoginThrottle()
