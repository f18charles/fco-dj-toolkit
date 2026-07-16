# authentication

A modular, reusable, and secure Django authentication package for the `fco-dj-kit` toolkit.

## Purpose

`authentication` implements core credential verification, brute-force security limits, email verification, and recovery mechanisms. Rather than locking down projects to a single auth setup, this module decouples core validation from credential issuance, allowing projects to configure one or more opt-in authentication methods.

It strictly separates concerns into two scopes:
1. **Core (`core/`)**: Standalone Django logic (throttling, password hashing, timing-attack mitigation, signals, token verification). Contains **zero** dependencies on external libraries like Django REST Framework (DRF) or SimpleJWT.
2. **Auth Methods (`auth_methods/`)**: Optional adapter layers (Session, DRF Token, SimpleJWT, OAuth2) that developers can select and include in their project's URLconf.

## Features

- **Brute-Force Protection**: Extensible lockout detection built on `LoginAttempt` logs.
- **Timing Mitigation**: Password checks run even when users don't exist, preventing username enumeration.
- **Email Verification & Password Recovery**: Stateless, secure token generation with automatic token invalidation upon email or password change.
- **Unified OAuth2 Flow**: OAuth2 identity resolution with built-in presets (Google, GitHub) that hands off credentials to Session, Token, or JWT issuance.
- **Custom Admin Interface**: Read-only admin panels for auditing `LoginAttempt`, `UserSession`, and `SocialAccount` entries.

---

## Installation

1. Copy (or install) the `authentication` package to your Django project root.
2. Add `authentication` and `common` (if not already present) to your `INSTALLED_APPS`:

   ```python
   INSTALLED_APPS = [
       ...
       "common",
       "users",
       "authentication",
   ]
   ```

3. Configure Django's Authentication Backends to use the case-insensitive username/email resolver:

   ```python
   AUTHENTICATION_BACKENDS = [
       "authentication.core.backends.EmailOrUsernameBackend",
   ]
   ```

4. Run migrations:

   ```bash
   python manage.py migrate
   ```

---

## Public Core API

### `authentication.core.services.AuthService`

| Method | Description |
| --- | --- |
| `verify_credentials(*, identifier, password, request=None)` | Verifies credentials (username or email). Throttles failed attempts, records `LoginAttempt`, and raises `AccountLockedError`, `InvalidCredentialsError`, or `AccountInactiveError`. |

### `authentication.core.services.PasswordService`

| Method | Description |
| --- | --- |
| `change_password(*, user, old_password, new_password)` | Validates new password strength, changes it, and fires `password_changed`. |
| `request_password_reset(*, identifier)` | Starts stateless password reset. Dispatches `password_reset_requested` with a token without leaking account existence. |
| `confirm_password_reset(*, uidb64, token, new_password)` | Validates the token and updates the password. |

### `authentication.core.services.EmailVerificationService`

| Method | Description |
| --- | --- |
| `request_verification(*, user)` | Dispatches `email_verification_requested` with the verification token and encoded ID. |
| `confirm_verification(*, uidb64, token)` | Validates the token, updates `is_email_verified = True` on the user model, and dispatches `email_verified`. |

---

## Opt-In Authentication Methods

Consuming projects map views from `auth_methods` in their URLconf according to their architecture:

### 1. Sessions (`auth_methods/session`)
Stateful, cookie-based Django sessions. Exposes endpoints for logging in, logging out, list active user sessions, and revoking sessions.
- **URLs**:
  ```python
  path("auth/session/", include("authentication.auth_methods.session.urls")),
  ```

### 2. DRF Tokens (`auth_methods/token`)
Standard Django REST Framework API token backend.
- **URLs**:
  ```python
  path("auth/token/", include("authentication.auth_methods.token.urls")),
  ```

### 3. JWT (`auth_methods/jwt`)
Stateless JSON Web Tokens via SimpleJWT. Supports automatic token blacklisting if `rest_framework_simplejwt.token_blacklist` is installed.
- **URLs**:
  ```python
  path("auth/jwt/", include("authentication.auth_methods.jwt.urls")),
  ```

### 4. OAuth2 (`auth_methods/oauth2`)
OAuth2 flow integration. Supports login redirection and callback resolving. Once verified, it hands off credential issuance to Session, Token, or JWT issuance.
- **Configuration**:
  Define `OAUTH2_PROVIDERS` in settings (e.g. google, github) and optionally `OAUTH2_DEFAULT_ISSUER`.
- **URLs**:
  ```python
  path("auth/oauth2/", include("authentication.auth_methods.oauth2.urls")),
  ```

---

## Security Throttling Settings

Brute-force protection can be configured via settings:
```python
# Instantiate custom LoginThrottle if defaults (5 attempts, 15 min lockout) need overriding
from authentication.core.throttling import LoginThrottle
# Example: 10 attempts within a 10 minute window, locking out for 30 minutes
custom_throttle = LoginThrottle(max_failed_attempts=10, window_minutes=10, lockout_minutes=30)
```

## Running Tests

Run the test suite using `pytest`:
```bash
uv run pytest authentication/
```
