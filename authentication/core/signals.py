from django.dispatch import Signal

# Sent after password verification and lockout checks pass, but before issuing any credential.
# A receiver (such as a 2FA module) can raise TwoFactorRequiredError to interrupt the login process.
# args: user, request
login_credentials_verified = Signal()

# Sent on successful login (credential issued)
# args: user, request
login_succeeded = Signal()

# Sent on failed authentication
# args: identifier, reason, request
login_failed = Signal()

# Sent when an identifier is locked out
# args: identifier, request
account_locked_out = Signal()

# Sent after user changes password
# args: user
password_changed = Signal()

# Sent when a password reset is requested
# args: user, token, uid
password_reset_requested = Signal()

# Sent when an email verification is requested
# args: user, token, uid
email_verification_requested = Signal()

# Sent when an email is successfully verified
# args: user
email_verified = Signal()

# Sent when a session is revoked
# args: user, session
session_revoked = Signal()

"""
Example: Future OTP (2FA) Signal Receiver Pattern

from django.dispatch import receiver
from authentication.core.signals import login_credentials_verified
from authentication.core.exceptions import TwoFactorRequiredError

@receiver(login_credentials_verified)
def require_otp(sender, user, request, **kwargs):
    if hasattr(user, "otp_profile") and user.otp_profile.is_enabled:
        # Create a challenge or fetch an existing one
        challenge_id = "some-uuid-or-challenge-id"
        raise TwoFactorRequiredError(
            message="OTP challenge is required to complete authentication.",
            challenge_id=challenge_id
        )
"""
