import pytest
from django.core.exceptions import ValidationError

from authentication.core.validators import validate_password_strength


def test_password_strength_valid() -> None:
    # A valid password that satisfies all requirements
    validate_password_strength("StrongPass123!")


def test_password_strength_missing_all() -> None:
    # A weak password that fails all checks
    with pytest.raises(ValidationError) as excinfo:
        validate_password_strength("")
    
    messages = excinfo.value.messages
    assert len(messages) == 5
    assert any("at least 10 characters" in msg for msg in messages)
    assert any("uppercase letter" in msg for msg in messages)
    assert any("lowercase letter" in msg for msg in messages)
    assert any("digit" in msg for msg in messages)
    assert any("special character" in msg for msg in messages)


def test_password_strength_missing_some() -> None:
    # Meets length but lacks uppercase, digit, and special character
    with pytest.raises(ValidationError) as excinfo:
        validate_password_strength("longlowercasestring")
    
    messages = excinfo.value.messages
    assert len(messages) == 3
    assert not any("at least 10 characters" in msg for msg in messages)
    assert any("uppercase letter" in msg for msg in messages)
    assert any("digit" in msg for msg in messages)
    assert any("special character" in msg for msg in messages)
