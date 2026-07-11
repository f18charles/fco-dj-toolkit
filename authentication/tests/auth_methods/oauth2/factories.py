import factory

from common.factories import BaseFactory
from users.tests.factories import UserFactory
from authentication.auth_methods.oauth2.models import SocialAccount


class SocialAccountFactory(BaseFactory):
    """
    Factory for producing SocialAccount records.
    """

    class Meta:
        model = SocialAccount

    user = factory.SubFactory(UserFactory)
    provider = "google"
    provider_user_id = factory.Sequence(lambda n: f"provider_user_{n}")
