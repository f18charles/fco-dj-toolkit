"""Tests for the selectors (read-only query) layer."""
import uuid

import pytest

from users.exceptions import UserNotFoundError
from users.selectors import (
    get_active_users,
    get_inactive_users,
    get_staff_users,
    get_user_by_email,
    get_user_by_id,
    get_users_by_ids,
)
from users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestGetUserById:
    def test_returns_matching_user(self):
        user = UserFactory()
        assert get_user_by_id(user.pk) == user

    def test_raises_when_not_found(self):
        with pytest.raises(UserNotFoundError):
            get_user_by_id(uuid.uuid4())


class TestGetUserByEmail:
    def test_returns_matching_user_case_insensitively(self):
        user = UserFactory(email="Mixed@Example.com")
        assert get_user_by_email("mixed@example.com") == user

    def test_raises_when_not_found(self):
        with pytest.raises(UserNotFoundError):
            get_user_by_email("missing@example.com")


class TestUserListSelectors:
    def test_get_active_users_excludes_inactive(self):
        UserFactory(username="activeselector", is_active=True)
        UserFactory(username="inactiveselector", is_active=False)
        assert get_active_users().count() == 1

    def test_get_inactive_users_excludes_active(self):
        UserFactory(username="activeselector2", is_active=True)
        UserFactory(username="inactiveselector2", is_active=False)
        assert get_inactive_users().count() == 1

    def test_get_staff_users_excludes_non_staff(self):
        UserFactory(username="staffselector", is_staff=True)
        UserFactory(username="nonstaffselector", is_staff=False)
        assert get_staff_users().count() == 1

    def test_get_users_by_ids_returns_only_requested_users(self):
        u1 = UserFactory()
        u2 = UserFactory()
        UserFactory()
        result_ids = set(get_users_by_ids([u1.pk, u2.pk]).values_list("pk", flat=True))
        assert result_ids == {u1.pk, u2.pk}
