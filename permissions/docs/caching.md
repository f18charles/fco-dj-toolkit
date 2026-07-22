# Permissions Caching Architecture

This document describes the caching layer in the `permissions` v2 module.

---

## 1. Overview & Caching Strategy

The `permissions` module implements a two-tier caching strategy:
1. **Per-Request In-Memory Cache**: Resolved user permissions are attached to `user._permissions_cache` for the duration of a request.
2. **Cross-Request Cache (Opt-in)**: Uses Django's cache framework (`django.core.cache`) to persist resolved global user permissions across HTTP requests and worker processes.

---

## 2. v1 In-Memory Cache vs v2 Cross-Request Cache

### v1 In-Memory Cache
- **Scope**: Attached directly to the Python `user` model instance in memory (`user._permissions_cache`).
- **Lifetime**: Request-scoped (discarded at end of request).
- **Limitations**: Every new HTTP request must re-query the database for user roles and permissions. Does not share state across worker processes or servers.

### v2 Cross-Request Cache
- **Scope**: Managed via Django's cache backend interface (`django.core.cache.caches`).
- **Cache Key Format**: `permissions:user:{user_pk}:all_perms`
- **Default TTL**: Configurable via `PERMISSIONS_CACHE_TTL` (default: `300` seconds / 5 minutes).
- **Fallback**: If `PERMISSIONS_CACHE_BACKEND` is not defined in Django settings, the module cleanly falls back to v1 per-request in-memory behavior.

---

## 3. Recommended Redis Configuration

To enable cross-request caching, configure a dedicated cache backend in `settings.py`:

```python
CACHES = {
    "default": { ... },
    "permissions": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "TIMEOUT": 300,
        "KEY_PREFIX": "fco_permissions",
    }
}

PERMISSIONS_CACHE_BACKEND = "permissions"
PERMISSIONS_CACHE_TTL = 300
```

---

## 4. What is Cached (and What is NOT)

### What IS Cached:
- **Global User Permissions**: Resolved set of direct active permission grants, active role assignments, inherited role permissions, and wildcard permissions.

### What is NOT Cached:
- **Object-Level Permissions (`ObjectPermission`)**: Checked dynamically per target object to prevent cache key explosion and ensure real-time access revocation on specific resources.
- **Scoped User Roles (`ScopedUserRole`)**: Evaluated on-demand per scope instance.

---

## 5. Cache Invalidation Guarantees

Automatic cache invalidation is triggered synchronously via Django `post_save` and `post_delete` signals connected to:
- `UserRole`
- `UserPermission`
- `ScopedUserRole`
- `ObjectPermission`

When any assignment changes or expires, `invalidate_user_permissions_cache(user)` immediately purges the cached permissions key for that user.

---

## 6. Testing with Caching

- **In Unit Tests**: LocMemCache (`django.core.cache.backends.locmem.LocMemCache`) can be used to verify cache behavior without external dependencies.
- **Disabling Cache in Tests**: Set `PERMISSIONS_CACHE_BACKEND = None` in test settings to test raw database resolution.
