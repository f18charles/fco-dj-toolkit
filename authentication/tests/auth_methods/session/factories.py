import factory

from common.factories import BaseFactory
from users.tests.factories import UserFactory
from authentication.auth_methods.session.models import UserSession


class UserSessionFactory(BaseFactory):
    """
    Factory for producing UserSession records.
    """

    class Meta:
        model = UserSession

    user = factory.SubFactory(UserFactory)
    session_key = factory.Sequence(lambda n: f"sessionkey{n:030d}")
    ip_address = factory.Faker("ipv4")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    is_active = True
