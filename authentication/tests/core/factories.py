import factory

from common.factories import BaseFactory
from users.tests.factories import UserFactory
from authentication.core.models import LoginAttempt


class LoginAttemptFactory(BaseFactory):
    """
    Factory for producing LoginAttempt records.
    """

    class Meta:
        model = LoginAttempt

    user = factory.SubFactory(UserFactory)
    identifier = factory.LazyAttribute(lambda obj: obj.user.email if obj.user else "nonexistent@example.com")
    ip_address = factory.Faker("ipv4")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    was_successful = False
    failure_reason = "invalid_credentials"
