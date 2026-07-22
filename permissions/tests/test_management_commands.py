import io
import pytest
from datetime import timedelta
from django.core.management import call_command
from django.utils import timezone
from permissions.models import UserRole, UserPermission, ScopedUserRole, ObjectPermission
from permissions.tests.factories import (
    UserRoleFactory,
    UserPermissionFactory,
    ScopedUserRoleFactory,
    ObjectPermissionFactory,
)


@pytest.mark.django_db
class TestCleanExpiredAssignmentsCommand:
    def test_dry_run_does_not_delete_records(self) -> None:
        now = timezone.now()
        past = now - timedelta(days=5)

        UserRoleFactory(expires_at=past)
        UserPermissionFactory(expires_at=past)
        ScopedUserRoleFactory(expires_at=past)
        ObjectPermissionFactory(expires_at=past)

        out = io.StringIO()
        call_command("clean_expired_assignments", "--dry-run", stdout=out)

        output = out.getvalue()
        assert "Dry run mode" in output
        assert "4 records would be deleted" in output or "Total: 4 records would be deleted" in output
        assert UserRole.objects.count() == 1
        assert UserPermission.objects.count() == 1
        assert ScopedUserRole.objects.count() == 1
        assert ObjectPermission.objects.count() == 1

    def test_clean_expired_assignments_without_dry_run(self) -> None:
        now = timezone.now()
        past = now - timedelta(days=5)
        future = now + timedelta(days=5)

        # Expired records
        ur_expired = UserRoleFactory(expires_at=past)
        up_expired = UserPermissionFactory(expires_at=past)
        sr_expired = ScopedUserRoleFactory(expires_at=past)
        op_expired = ObjectPermissionFactory(expires_at=past)

        # Non-expired records
        ur_active = UserRoleFactory(expires_at=future)
        up_active = UserPermissionFactory(expires_at=future)
        sr_active = ScopedUserRoleFactory(expires_at=future)
        op_active = ObjectPermissionFactory(expires_at=future)

        out = io.StringIO()
        call_command("clean_expired_assignments", stdout=out)

        assert UserRole.objects.filter(id=ur_expired.id).exists() is False
        assert UserPermission.objects.filter(id=up_expired.id).exists() is False
        assert ScopedUserRole.objects.filter(id=sr_expired.id).exists() is False
        assert ObjectPermission.objects.filter(id=op_expired.id).exists() is False

        assert UserRole.objects.filter(id=ur_active.id).exists() is True
        assert UserPermission.objects.filter(id=up_active.id).exists() is True
        assert ScopedUserRole.objects.filter(id=sr_active.id).exists() is True
        assert ObjectPermission.objects.filter(id=op_active.id).exists() is True

    def test_older_than_flag(self) -> None:
        now = timezone.now()
        expired_3_days_ago = now - timedelta(days=3)
        expired_10_days_ago = now - timedelta(days=10)

        ur_3days = UserRoleFactory(expires_at=expired_3_days_ago)
        ur_10days = UserRoleFactory(expires_at=expired_10_days_ago)

        out = io.StringIO()
        call_command("clean_expired_assignments", "--older-than=7", stdout=out)

        # 3 days ago is NOT older than 7 days, so it remains
        assert UserRole.objects.filter(id=ur_3days.id).exists() is True
        # 10 days ago IS older than 7 days, so it is deleted
        assert UserRole.objects.filter(id=ur_10days.id).exists() is False
