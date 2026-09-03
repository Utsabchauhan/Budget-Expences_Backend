import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from core.models import UserProfile


class Command(BaseCommand):
    help = "Create or update the default BudgetFlow admin user."

    def add_arguments(self, parser):
        parser.add_argument("--password", help="Admin password. Prefer BUDGETFLOW_ADMIN_PASSWORD in local shells.")

    def handle(self, *args, **options):
        password = options.get("password") or os.getenv("BUDGETFLOW_ADMIN_PASSWORD")
        if not password:
            raise CommandError("Provide --password or set BUDGETFLOW_ADMIN_PASSWORD.")

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@budgetflow.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        user.email = "admin@budgetflow.com"
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = UserProfile.Role.ADMIN
        profile.save(update_fields=["role", "updated_at"])

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} admin user."))
