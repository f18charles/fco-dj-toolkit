from django.contrib.auth.tokens import PasswordResetTokenGenerator as DjangoPasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from authentication.core.exceptions import InvalidTokenError


class PasswordResetTokenGenerator(DjangoPasswordResetTokenGenerator):
    """
    Token generator for password resets.
    Uses a distinct salt to avoid token re-use across verification mechanisms.
    """
    key_salt = "authentication.core.PasswordResetTokenGenerator"


class EmailVerificationTokenGenerator(DjangoPasswordResetTokenGenerator):
    """
    Token generator for email verification.
    Includes the email in the hash value to invalidate the token if the email changes.
    """
    key_salt = "authentication.core.EmailVerificationTokenGenerator"

    def _make_hash_value(self, user, timestamp: int) -> str:
        login_timestamp = (
            ""
            if user.last_login is None
            else user.last_login.replace(microsecond=0).isoformat()
        )
        email = user.email or ""
        return f"{user.pk}{user.password}{login_timestamp}{timestamp}{email}"


# Instances to be used across services
password_reset_token_generator = PasswordResetTokenGenerator()
email_verification_token_generator = EmailVerificationTokenGenerator()


def encode_uid(pk) -> str:
    """
    Encode a primary key into a urlsafe base64 string.
    """
    return urlsafe_base64_encode(force_bytes(pk))


def decode_uid(uidb64: str) -> str:
    """
    Decode a urlsafe base64 string into a primary key representation.
    Raises InvalidTokenError if decoding fails.
    """
    try:
        return force_str(urlsafe_base64_decode(uidb64))
    except (ValueError, TypeError, UnicodeDecodeError) as e:
        raise InvalidTokenError("The user ID in the link is invalid.") from e
