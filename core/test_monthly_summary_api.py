from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from budgets.models import Budget
from categories.models import Category
from departments.models import Department
from expenses.models import Expense
from income.models import Income
from reports.models import BudgetSummary
from core.models import UserProfile


def run_background_job_immediately(function, *args, **kwargs):
    function(*args, **kwargs)


class MonthlySummaryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="summary-user", password="test-pass")
        self.user.profile.role = UserProfile.Role.ADMIN
        self.user.profile.save(update_fields=["role", "updated_at"])
        self.client.force_authenticate(user=self.user)
        self.department = Department.objects.create(name="Technology", code="TECH")
        self.zero_budget_department = Department.objects.create(name="Operations", code="OPS")
        self.expense_category = Category.objects.create(name="Software", type=Category.Type.EXPENSE)
        self.income_category = Category.objects.create(name="Service Revenue", type=Category.Type.INCOME)
        self.budget = Budget.objects.create(
            name="September Software Budget",
            department=self.department,
            category=self.expense_category,
            amount=Decimal("1000.00"),
            start_date="2026-09-01",
            end_date="2026-09-30",
            created_by=self.user,
        )
        Expense.objects.create(
            expense_number="EXP-100001",
            user=self.user,
            department=self.department,
            category=self.expense_category,
            budget=self.budget,
            title="IDE subscription",
            amount=Decimal("250.00"),
            expense_date="2026-09-05",
            payment_method=Expense.PaymentMethod.CARD,
            status=Expense.Status.APPROVED,
        )
        Expense.objects.create(
            expense_number="EXP-100002",
            user=self.user,
            department=self.department,
            category=self.expense_category,
            budget=self.budget,
            title="Cloud hosting",
            amount=Decimal("150.00"),
            expense_date="2026-09-15",
            payment_method=Expense.PaymentMethod.BANK_TRANSFER,
            status=Expense.Status.APPROVED,
        )
        Expense.objects.create(
            expense_number="EXP-100003",
            user=self.user,
            department=self.zero_budget_department,
            category=self.expense_category,
            title="Operations supplies",
            amount=Decimal("25.00"),
            expense_date="2026-09-10",
            payment_method=Expense.PaymentMethod.CASH,
            status=Expense.Status.APPROVED,
        )
        Income.objects.create(
            income_number="INC-100001",
            user=self.user,
            department=self.department,
            category=self.income_category,
            source="Implementation revenue",
            amount=Decimal("700.00"),
            income_date="2026-09-08",
            status=Income.Status.CONFIRMED,
        )
        Income.objects.create(
            income_number="INC-100002",
            user=self.user,
            department=self.department,
            category=self.income_category,
            source="Out-of-month revenue",
            amount=Decimal("999.00"),
            income_date="2026-08-31",
            status=Income.Status.CONFIRMED,
        )

    def generate_summary(self):
        with (
            patch("reports.services.close_old_connections"),
            patch("reports.services.summary_executor.submit", side_effect=run_background_job_immediately),
        ):
            return self.client.post(
                reverse("monthly-summary-generate"),
                {"month": 9, "year": 2026},
                format="json",
            )

    def test_trigger_returns_202_and_calculates_department_summary(self):
        response = self.generate_summary()

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(response.data["success"])
        self.assertEqual(BudgetSummary.objects.count(), 2)

        summary = BudgetSummary.objects.get(department=self.department, month=9, year=2026)
        self.assertEqual(summary.status, BudgetSummary.Status.COMPLETED)
        self.assertEqual(summary.total_budget, Decimal("1000.00"))
        self.assertEqual(summary.total_expense, Decimal("400.00"))
        self.assertEqual(summary.total_income, Decimal("700.00"))
        self.assertEqual(summary.remaining_budget, Decimal("600.00"))
        self.assertEqual(summary.utilization_percentage, Decimal("40.00"))

    def test_zero_budget_is_safe(self):
        self.generate_summary()

        summary = BudgetSummary.objects.get(department=self.zero_budget_department, month=9, year=2026)
        self.assertEqual(summary.status, BudgetSummary.Status.COMPLETED)
        self.assertEqual(summary.total_budget, Decimal("0.00"))
        self.assertEqual(summary.total_expense, Decimal("25.00"))
        self.assertEqual(summary.remaining_budget, Decimal("-25.00"))
        self.assertEqual(summary.utilization_percentage, Decimal("0.00"))

    def test_invalid_month_returns_validation_error(self):
        response = self.client.post(
            reverse("monthly-summary-generate"),
            {"month": 13, "year": 2026},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("month", response.data["errors"])

    def test_repeated_generation_updates_existing_summary(self):
        self.generate_summary()
        Expense.objects.create(
            expense_number="EXP-100004",
            user=self.user,
            department=self.department,
            category=self.expense_category,
            budget=self.budget,
            title="Monitoring tool",
            amount=Decimal("100.00"),
            expense_date="2026-09-20",
            payment_method=Expense.PaymentMethod.CARD,
            status=Expense.Status.APPROVED,
        )

        self.generate_summary()

        self.assertEqual(BudgetSummary.objects.filter(department=self.department, month=9, year=2026).count(), 1)
        summary = BudgetSummary.objects.get(department=self.department, month=9, year=2026)
        self.assertEqual(summary.status, BudgetSummary.Status.COMPLETED)
        self.assertEqual(summary.total_expense, Decimal("500.00"))
        self.assertEqual(summary.remaining_budget, Decimal("500.00"))
        self.assertEqual(summary.utilization_percentage, Decimal("50.00"))

    def test_list_filters_and_detail_endpoint_return_summaries(self):
        self.generate_summary()

        list_response = self.client.get(
            reverse("monthly-summary-list"),
            {"month": 9, "year": 2026, "department": self.department.id},
        )
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data["data"]), 1)
        self.assertEqual(list_response.data["data"][0]["department"], self.department.id)

        summary_id = list_response.data["data"][0]["id"]
        detail_response = self.client.get(reverse("monthly-summary-detail", args=[summary_id]))
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data["data"]["status"], BudgetSummary.Status.COMPLETED)
