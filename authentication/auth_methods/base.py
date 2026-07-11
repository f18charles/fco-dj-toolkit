from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AuthMethodProtocol(Protocol):
    """
    Structural Protocol documenting the conventions for authentication methods.
    It is not enforced by inheritance, but used as a typing blueprint.
    """

    def issue(self, user: Any, request: Any) -> dict:
        """
        Issue credentials for the authenticated user.
        Returns a dictionary containing the payload (tokens, keys, etc.).
        """
        ...

    def revoke(self, credential: Any, request: Any) -> None:
        """
        Revoke the specified credential.
        """
        ...
