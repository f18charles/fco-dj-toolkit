import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from common.exceptions import ValidationException
from authentication.core.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    EmailAlreadyVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    TwoFactorRequiredError,
)
from authentication.core.services import AuthService, PasswordService, EmailVerificationService
from authentication.core.signals import (
    login_credentials_verified,
    login_failed,
    account_locked_out,
    password_reset_requested,
    email_verification_requested,
    email_verified,
)
from authentication.core.throttling import default_login_throttle
from authentication.core.tokens import (
    email_verification_token_generator,
    encode_uid,
    password_reset_token_generator,
)
from users.tests.factories import UserFactory

User = get_user_model()


@pytest.fixture(autouse=True)
def clear_login_throttle() -> None:
    # Clear login attempts in DB between tests
    from authentication.core.models import LoginAttempt
    LoginAttempt.objects.all().delete()


@pytest.mark.django_db
def test_verify_credentials_success() -> None:
    user = UserFactory(username="testuser", password="StrongPass123!")
    
    # Successful login returns user
    authenticated = AuthService.verify_credentials(identifier="testuser", password="StrongPass123!")
    assert authenticated == user


@pytest.mark.django_db
def test_verify_credentials_wrong_password() -> None:
    UserFactory(username="testuser", password="StrongPass123!")

    # Verify signal is triggered
    login_failed_triggered = False

    def on_failed_login(sender, **kwargs):
        nonlocal login_failed_triggered
        login_failed_triggered = True

    login_failed.connect(on_failed_login)

    try:
        with pytest.raises(InvalidCredentialsError):
            AuthService.verify_credentials(identifier="testuser", password="WrongPassword")
        
        assert login_failed_triggered
    finally:
        login_failed.disconnect(on_failed_login)


@pytest.mark.django_db
def test_verify_credentials_locked_out() -> None:
    UserFactory(username="testuser", password="StrongPass123!")
    
    # Fail 5 times to trigger lockout
    for _ in range(5):
        try:
            AuthService.verify_credentials(identifier="testuser", password="WrongPassword")
        except InvalidCredentialsError:
            pass

    locked_out_triggered = False

    def on_lockout(sender, **kwargs):
        nonlocal locked_out_triggered
        locked_out_triggered = True

    account_locked_out.connect(on_lockout)

    try:
        with pytest.raises(AccountLockedError) as excinfo:
            AuthService.verify_credentials(identifier="testuser", password="StrongPass123!")
        
        assert excinfo.value.retry_after_seconds > 0
        assert locked_out_triggered
    finally:
        account_locked_out.disconnect(on_lockout)


@pytest.mark.django_db
def test_verify_credentials_inactive_account() -> None:
    user = UserFactory(username="inactiveuser", password="StrongPass123!", is_active=False)

    with pytest.raises(AccountInactiveError):
        AuthService.verify_credentials(identifier="inactiveuser", password="StrongPass123!")


@pytest.mark.django_db
def test_verify_credentials_2fa_hook_propagation() -> None:
    UserFactory(username="testuser", password="StrongPass123!")

    def raise_2fa_error(sender, user, **kwargs):
        raise TwoFactorRequiredError(challenge_id="test-challenge")

    login_credentials_verified.connect(raise_2fa_error)

    try:
        with pytest.raises(TwoFactorRequiredError) as excinfo:
            AuthService.verify_credentials(identifier="testuser", password="StrongPass123!")
        
        assert excinfo.value.challenge_id == "test-challenge"
    finally:
        login_credentials_verified.disconnect(raise_2fa_error)


@pytest.mark.django_db
def test_change_password_success() -> None:
    user = UserFactory(password="OldStrongPass1!")
    
    PasswordService.change_password(user=user, old_password="OldStrongPass1!", new_password="NewStrongPass2@")
    
    assert user.check_password("NewStrongPass2@")


@pytest.mark.django_db
def test_change_password_wrong_old_password() -> None:
    user = UserFactory(password="OldStrongPass1!")
    
    with pytest.raises(InvalidCredentialsError):
        PasswordService.change_password(user=user, old_password="WrongOldPassword", new_password="NewStrongPass2@")


@pytest.mark.django_db
def test_change_password_weak_new_password() -> None:
    user = UserFactory(password="OldStrongPass1!")
    
    with pytest.raises(ValidationException):
        PasswordService.change_password(user=user, old_password="OldStrongPass1!", new_password="weak")


@pytest.mark.django_db
def test_password_reset_flow() -> None:
    user = UserFactory(email="reset@example.com")
    
    # Store sent token/uid
    reset_data = {}

    def on_reset_requested(sender, user, token, uid, **kwargs):
        reset_data["token"] = token
        reset_data["uid"] = uid

    password_reset_requested.connect(on_reset_requested)

    try:
        # Request password reset
        PasswordService.request_password_reset(identifier="reset@example.com")
        
        assert "token" in reset_data
        assert "uid" in reset_data

        # Confirm reset
        PasswordService.confirm_password_reset(
            uidb64=reset_data["uid"],
            token=reset_data["token"],
            new_password="NewResetPassword123!",
        )
        
        user.refresh_from_db()
        assert user.check_password("NewResetPassword123!")
    finally:
        password_reset_requested.disconnect(on_reset_requested)


@pytest.mark.django_db
def test_password_reset_invalid_or_expired_token() -> None:
    user = UserFactory(email="reset@example.com")
    uid = encode_uid(user.pk)
    
    with pytest.raises(InvalidTokenError):
        PasswordService.confirm_password_reset(
            uidb64=uid,
            token="invalid-token",
            new_password="NewResetPassword123!",
        )


@pytest.mark.django_db
def test_email_verification_flow() -> None:
    user = UserFactory(email="verify@example.com")
    # Simulate custom attribute on user model
    user.is_email_verified = False
    
    verify_data = {}

    def on_verification_requested(sender, user, token, uid, **kwargs):
        verify_data["token"] = token
        verify_data["uid"] = uid

    email_verification_requested.connect(on_verification_requested)

    verified_user_instance = None

    def on_email_verified(sender, user, **kwargs):
        nonlocal verified_user_instance
        verified_user_instance = user

    email_verified.connect(on_email_verified)

    try:
        # Request verification
        EmailVerificationService.request_verification(user=user)
        
        assert "token" in verify_data
        assert "uid" in verify_data

        # Confirm verification
        EmailVerificationService.confirm_verification(
            uidb64=verify_data["uid"],
            token=verify_data["token"],
        )
        
        assert verified_user_instance == user
        # Check if attribute got updated
        assert getattr(user, "is_email_verified", False) is True
    finally:
        email_verification_requested.disconnect(on_verification_requested)
        email_verified.disconnect(on_email_verified)


@pytest.mark.django_db
def test_email_verification_already_verified() -> None:
    user = UserFactory(email="already@example.com")
    user.is_email_verified = True
    
    with pytest.raises(EmailAlreadyVerifiedError):
        EmailVerificationService.request_verification(user=user)
