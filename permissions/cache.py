from typing import Set, Optional
from django.conf import settings
from django.core.cache import caches, InvalidCacheBackendError


def _get_cache():
    cache_name = getattr(settings, "PERMISSIONS_CACHE_BACKEND", None)
    if not cache_name:
        return None
    try:
        return caches[cache_name]
    except (InvalidCacheBackendError, KeyError):
        return None


def get_user_permissions_from_cache(user) -> Optional[Set[str]]:
    """
    Return the cached permission set for user, or None if not cached.
    Checks configured Django cache backend first, then falls back to None.
    """
    cache = _get_cache()
    if not cache:
        return None
    key = f"permissions:user:{user.pk}:all_perms"
    cached = cache.get(key)
    if cached is not None:
        return set(cached)
    return None


def set_user_permissions_cache(user, permissions: Set[str]) -> None:
    """Store the resolved permission set in the configured cache backend."""
    cache = _get_cache()
    if not cache:
        return
    key = f"permissions:user:{user.pk}:all_perms"
    ttl = getattr(settings, "PERMISSIONS_CACHE_TTL", 300)
    cache.set(key, list(permissions), ttl)


def invalidate_user_permissions_cache(user) -> None:
    """
    Delete all cached permission data for user from configured cache backend.
    """
    cache = _get_cache()
    if not cache:
        return
    key = f"permissions:user:{user.pk}:all_perms"
    try:
        cache.delete(key)
    except Exception:
        pass
