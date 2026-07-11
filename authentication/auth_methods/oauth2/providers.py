from dataclasses import dataclass
from typing import List


@dataclass
class OAuth2ProviderConfig:
    """
    Configuration data class for an OAuth2 provider.
    """

    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scopes: List[str]
