from __future__ import annotations

from typing import Any, Optional

from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import MultipleObjectsReturned, ValidationError
from django.db import models
from django.http import HttpRequest

from common.exceptions import ValidationException
from authentication.core.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    EmailAlreadyVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from authentication.core.signals import (
    account_locked_out,
    email_verification_requested,
    email_verified,
    login_credentials_verified,
    login_failed,
    password_changed,
    password_reset_requested,
)
from authentication.core.throttling import default_login_throttle
from authentication.core.tokens import (
    decode_uid,
    email_verification_token_generator,
    encode_uid,
    password_reset_token_generator,
)
from authentication.core.validators import validate_password_strength

User = get_user_model()


class AuthService:
    """
    Handles core authentication logic, including lockout verification
    and credential validation.
    """

    @staticmethod
    def verify_credentials(
        *,
        identifier: str,
        password: str,
        request: Optional[HttpRequest] = None,
    ) -> Any:
        """
        Verify the username/email and password combination.
        Performs lockout checks and records all attempts.

        Raises:
            AccountLockedError: if the identifier is locked out.
            InvalidCredentialsError: if authentication fails.
            AccountInactiveError: if user is disabled.
        """
        # 1. Lockout Check
        if default_login_throttle.is_locked_out(identifier):
            retry_after = default_login_throttle.seconds_until_unlock(identifier)
            account_locked_out.send(
                sender=AuthService,
                identifier=identifier,
                request=request,
            )
            raise AccountLockedError(
                message=f"Account temporarily locked due to too many failed attempts. Try again in {retry_after} seconds.",
                retry_after_seconds=retry_after,
            )

        # 2. Authenticate
        user = authenticate(request=request, username=identifier, password=password)

        if user is None:
            # Record failed login attempt
            default_login_throttle.record_attempt(
                identifier=identifier,
                was_successful=False,
                request=request,
                failure_reason="invalid_credentials",
            )
            login_failed.send(
                sender=AuthService,
                identifier=identifier,
                reason="invalid_credentials",
                request=request,
            )
            raise InvalidCredentialsError()

        # 3. Check if user is active
        if not user.is_active:
            default_login_throttle.record_attempt(
                identifier=identifier,
                was_successful=False,
                request=request,
                user=user,
                failure_reason="account_inactive",
            )
            login_failed.send(
                sender=AuthService,
                identifier=identifier,
                reason="account_inactive",
                request=request,
            )
            raise AccountInactiveError()

        # 4. Successful credentials verification
        default_login_throttle.record_attempt(
            identifier=identifier,
            was_successful=True,
            request=request,
            user=user,
        )

        # Send signal. Let any TwoFactorRequiredError propagate uncaught.
        login_credentials_verified.send(
            sender=AuthService,
            user=user,
            request=request,
        )

        return user


class PasswordService:
    """
    Handles password changes and stateless password reset workflows.
    """

    @staticmethod
    def change_password(*, user: Any, old_password: str, new_password: str) -> None:
        """
        Change user's password after verifying the old password.

        Raises:
            InvalidCredentialsError: if old password is incorrect.
            ValidationException: if new password fails validation rules.
        """
        if not user.check_password(old_password):
            raise InvalidCredentialsError("Old password is incorrect.")

        try:
            validate_password_strength(new_password)
        except ValidationError as e:
            errors = e.message_list if hasattr(e, "message_list") else e.messages
            raise ValidationException(
                message="New password does not meet complexity requirements.",
                errors=errors,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])
        password_changed.send(sender=PasswordService, user=user)

    @staticmethod
    def request_password_reset(*, identifier: str) -> None:
        """
        Initiate a password reset flow. Does not leak account existence.
        """
        try:
            # Support lookup by username or email (case-insensitive)
            user = User.objects.get(
                models.Q(username__iexact=identifier) | models.Q(email__iexact=identifier)
            )
        except (User.DoesNotExist, MultipleObjectsReturned):
            # Silently return to prevent user enumeration
            return

        token = password_reset_token_generator.make_token(user)
        uid = encode_uid(user.pk)

        password_reset_requested.send(
            sender=PasswordService,
            user=user,
            token=token,
            uid=uid,
        )

    @staticmethod
    def confirm_password_reset(*, uidb64: str, token: str, new_password: str) -> None:
        """
        Confirm password reset using base64 encoded uid and generator token.

        Raises:
            InvalidTokenError: if uid is corrupt or token is invalid/expired.
            ValidationException: if new password fails validation rules.
        """
        pk = decode_uid(uidb64)

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise InvalidTokenError("The password reset link is invalid or expired.")

        if not password_reset_token_generator.check_token(user, token):
            raise InvalidTokenError("The password reset link is invalid or expired.")

        try:
            validate_password_strength(new_password)
        except ValidationError as e:
            errors = e.message_list if hasattr(e, "message_list") else e.messages
            raise ValidationException(
                message="New password does not meet complexity requirements.",
                errors=errors,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])
        password_changed.send(sender=PasswordService, user=user)


class EmailVerificationService:
    """
    Handles email verification flow using stateless tokens.
    """

    @staticmethod
    def request_verification(*, user: Any) -> None:
        """
        Request verification email for a user.

        Raises:
            EmailAlreadyVerifiedError: if user's email is already verified.
        """
        if getattr(user, "is_email_verified", False):
            raise EmailAlreadyVerifiedError("Email is already verified.")

        token = email_verification_token_generator.make_token(user)
        uid = encode_uid(user.pk)

        email_verification_requested.send(
            sender=EmailVerificationService,
            user=user,
            token=token,
            uid=uid,
        )

    @staticmethod
    def confirm_verification(*, uidb64: str, token: str) -> None:
        """
        Confirm email verification using base64 encoded uid and verification token.

        Raises:
            InvalidTokenError: if token is invalid or user is not found.
            EmailAlreadyVerifiedError: if the email was already verified.
        """
        pk = decode_uid(uidb64)

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise InvalidTokenError("The verification link is invalid or expired.")

        if getattr(user, "is_email_verified", False):
            raise EmailAlreadyVerifiedError("Email is already verified.")

        if not email_verification_token_generator.check_token(user, token):
            raise InvalidTokenError("The verification link is invalid or expired.")

        # Update if attribute is present on the custom User model
        if hasattr(user, "is_email_verified"):
            user.is_email_verified = True
            from django.core.exceptions import FieldDoesNotExist
            try:
                user._meta.get_field("is_email_verified")
                user.save(update_fields=["is_email_verified"])
            except FieldDoesNotExist:
                # Dynamic attribute or property, not mapped to a database column
                pass

        email_verified.send(sender=EmailVerificationService, user=user)
