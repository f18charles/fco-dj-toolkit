from datetime import timedelta
import pytest
from django.utils import timezone

from authentication.core.throttling import LoginThrottle
from authentication.tests.core.factories import LoginAttemptFactory
from users.tests.factories import UserFactory


@pytest.mark.django_db
def test_failed_attempt_count() -> None:
    throttle = LoginThrottle(max_failed_attempts=3, window_minutes=5)
    identifier = "throttle_test@example.com"
    
    assert throttle.failed_attempt_count(identifier) == 0
    
    # Record a failed attempt
    throttle.record_attempt(identifier=identifier, was_successful=False)
    assert throttle.failed_attempt_count(identifier) == 1

    # Record a successful attempt
    throttle.record_attempt(identifier=identifier, was_successful=True)
    # The count of consecutive failed attempts should reset to 0
    assert throttle.failed_attempt_count(identifier) == 0

    # Record two more failed attempts
    throttle.record_attempt(identifier=identifier, was_successful=False)
    throttle.record_attempt(identifier=identifier, was_successful=False)
    assert throttle.failed_attempt_count(identifier) == 2


@pytest.mark.django_db
def test_lockout_trigger_and_timing() -> None:
    throttle = LoginThrottle(max_failed_attempts=3, window_minutes=15, lockout_minutes=15)
    identifier = "lockout_test@example.com"

    # Make failed attempts up to the limit
    throttle.record_attempt(identifier=identifier, was_successful=False)
    throttle.record_attempt(identifier=identifier, was_successful=False)
    assert not throttle.is_locked_out(identifier)

    # Third failed attempt triggers lockout
    throttle.record_attempt(identifier=identifier, was_successful=False)
    assert throttle.is_locked_out(identifier)
    
    seconds = throttle.seconds_until_unlock(identifier)
    assert 0 < seconds <= 900


@pytest.mark.django_db
def test_lockout_expiry() -> None:
    throttle = LoginThrottle(max_failed_attempts=2, window_minutes=15, lockout_minutes=15)
    identifier = "expiry_test@example.com"

    # Record attempts that are older than lockout_minutes
    attempt1 = throttle.record_attempt(identifier=identifier, was_successful=False)
    attempt2 = throttle.record_attempt(identifier=identifier, was_successful=False)
    assert throttle.is_locked_out(identifier)

    # Manually backdate the attempts in the DB to simulate passage of time
    past_time = timezone.now() - timedelta(minutes=16)
    attempt1.created_at = past_time
    attempt1.save()
    attempt2.created_at = past_time
    attempt2.save()

    # The throttle should register that lockout has expired
    assert not throttle.is_locked_out(identifier)
    assert throttle.seconds_until_unlock(identifier) == 0
