from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from permissions.models import UserRole, UserPermission, ScopedUserRole, ObjectPermission


class Command(BaseCommand):
    help = "Clean up expired UserRole, UserPermission, ScopedUserRole, and ObjectPermission assignments."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print counts of records that would be deleted without actually deleting them.",
        )
        parser.add_argument(
            "--older-than",
            type=int,
            default=0,
            help="Only delete assignments that expired more than N days ago (default: 0).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry-run"]
        older_than_days = options["older-than"]
        now = timezone.now()
        cutoff_date = now - timedelta(days=older_than_days)

        if dry_run:
            self.stdout.write("Dry run mode - no records will be deleted.")

        models_to_clean = [
            ("UserRole", UserRole),
            ("UserPermission", UserPermission),
            ("ScopedUserRole", ScopedUserRole),
            ("ObjectPermission", ObjectPermission),
        ]

        total_deleted_count = 0

        for name, model_cls in models_to_clean:
            qs = model_cls.objects.filter(expires_at__isnull=False, expires_at__lte=cutoff_date)
            count = qs.count()

            if dry_run:
                self.stdout.write(
                    f"{name}: {count} expired records would be deleted (older than {older_than_days} days)"
                )
            else:
                deleted_count, _ = qs.delete()
                self.stdout.write(
                    f"{name}: {deleted_count} expired records deleted (older than {older_than_days} days)"
                )
                count = deleted_count

            total_deleted_count += count

        msg_action = "would be deleted" if dry_run else "deleted"
        self.stdout.write(f"Total: {total_deleted_count} records {msg_action}.")
