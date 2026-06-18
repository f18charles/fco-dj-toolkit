import uuid
from typing import Any, Iterable, List, TypeVar

T = TypeVar("T")


def generate_uuid() -> uuid.UUID:
    """
    Generate a random UUID v4.
    """
    return uuid.uuid4()


def normalize_email(email: str) -> str:
    """
    Normalize the email address by lowercasing the domain part.
    """
    email = email or ""
    email = email.strip()
    if "@" in email:
        email_name, domain_part = email.rsplit("@", 1)
        email = f"{email_name}@{domain_part.lower()}"
    return email


def safe_getattr(obj: Any, path: str, default: Any = None) -> Any:
    """
    Safely get nested attributes from an object.

    Example:
        safe_getattr(user, "profile.address.city", default="Unknown")
    """
    attributes = path.split(".")
    for attr in attributes:
        try:
            obj = getattr(obj, attr)
        except AttributeError:
            return default
    return obj


def chunk_list(lst: Iterable[T], chunk_size: int) -> List[List[T]]:
    """
    Split an iterable into chunks of a maximum size.

    Example:
        chunk_list([1, 2, 3, 4, 5], 2) -> [[1, 2], [3, 4], [5]]
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than zero.")
    lst_list = list(lst)
    return [lst_list[i : i + chunk_size] for i in range(0, len(lst_list), chunk_size)]
