from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from approvals.models import Approval
from budgets.models import Budget
from categories.models import Category
from departments.models import Department
from expenses.models import Expense
from core.models import UserProfile


class ComplexReportAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="rita",
            first_name="Rita",
            last_name="Shrestha",
            password="test-pass",
        )
        self.user.profile.role = UserProfile.Role.ADMIN
        self.user.profile.save(update_fields=["role", "updated_at"])
        self.client.force_authenticate(user=self.user)
        self.approver = user_model.objects.create_user(username="approver", password="test-pass")
        self.department = Department.objects.create(name="Technology", code="TECH")
        self.other_department = Department.objects.create(name="Operations", code="OPS")
        self.category = Category.objects.create(name="Software", type=Category.Type.EXPENSE)
        self.travel_category = Category.objects.create(name="Travel", type=Category.Type.EXPENSE)
        self.budget = Budget.objects.create(
            name="Software Budget",
            department=self.department,
            category=self.category,
            amount=Decimal("1000.00"),
            start_date="2026-01-01",
            end_date="2026-12-31",
            created_by=self.user,
        )
        self.empty_budget = Budget.objects.create(
            name="Travel Budget",
            department=self.department,
            category=self.travel_category,
            amount=Decimal("500.00"),
            start_date="2026-01-01",
            end_date="2026-12-31",
            created_by=self.user,
        )
        self.over_budget = Budget.objects.create(
            name="Operations Software Budget",
            department=self.other_department,
            category=self.category,
            amount=Decimal("100.00"),
            start_date="2026-01-01",
            end_date="2026-12-31",
            created_by=self.user,
        )
        self.approved_expense = self.create_expense(
            "EXP-000001",
            self.budget,
            self.category,
            Decimal("250.00"),
            Expense.Status.APPROVED,
            "2026-02-01",
        )
        self.pending_expense = self.create_expense(
            "EXP-000002",
            self.budget,
            self.category,
            Decimal("150.00"),
            Expense.Status.PENDING,
            "2026-02-02",
        )
        self.rejected_expense = self.create_expense(
            "EXP-000003",
            None,
            self.travel_category,
            Decimal("50.00"),
            Expense.Status.REJECTED,
            "2026-03-01",
        )
        self.create_expense(
            "EXP-000004",
            self.over_budget,
            self.category,
            Decimal("125.00"),
            Expense.Status.APPROVED,
            "2026-02-05",
            department=self.other_department,
        )
        Approval.objects.create(
            expense=self.approved_expense,
            approver=self.approver,
            status=Approval.Status.APPROVED,
        )
        Approval.objects.create(
            expense=self.pending_expense,
            approver=self.approver,
            status=Approval.Status.PENDING,
        )
        Approval.objects.create(
            expense=self.rejected_expense,
            approver=self.approver,
            status=Approval.Status.REJECTED,
        )

    def create_expense(
        self,
        expense_number,
        budget,
        category,
        amount,
        expense_status,
        expense_date,
        department=None,
    ):
        return Expense.objects.create(
            expense_number=expense_number,
            user=self.user,
            department=department or self.department,
            category=category,
            budget=budget,
            title=f"Expense {expense_number}",
            amount=amount,
            expense_date=expense_date,
            payment_method=Expense.PaymentMethod.CARD,
            status=expense_status,
        )

    def test_budget_utilization_calculation(self):
        response = self.client.get(reverse("budget-utilization-report"), {"department": self.department.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        software = next(item for item in response.data["data"] if item["category"] == "Software")
        self.assertEqual(software["department"], "Technology")
        self.assertEqual(software["allocated_budget"], "1000.00")
        self.assertEqual(software["total_expense"], "400.00")
        self.assertEqual(software["remaining_budget"], "600.00")
        self.assertEqual(software["utilization_percentage"], "40.00")
        self.assertEqual(software["status"], "NORMAL")

    def test_budget_utilization_over_budget_case(self):
        response = self.client.get(
            reverse("budget-utilization-report"),
            {"department": self.other_department.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.data["data"][0]
        self.assertEqual(report["allocated_budget"], "100.00")
        self.assertEqual(report["total_expense"], "125.00")
        self.assertEqual(report["remaining_budget"], "-25.00")
        self.assertEqual(report["utilization_percentage"], "125.00")
        self.assertEqual(report["status"], "OVER_BUDGET")

    def test_budget_utilization_no_expense_case(self):
        response = self.client.get(reverse("budget-utilization-report"), {"department": self.department.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        travel = next(item for item in response.data["data"] if item["category"] == "Travel")
        self.assertEqual(travel["allocated_budget"], "500.00")
        self.assertEqual(travel["total_expense"], "0.00")
        self.assertEqual(travel["remaining_budget"], "500.00")
        self.assertEqual(travel["utilization_percentage"], "0.00")
        self.assertEqual(travel["status"], "NORMAL")

    def test_employee_summary(self):
        response = self.client.get(reverse("employee-summary-report"), {"department": self.department.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        report = response.data["data"][0]
        self.assertEqual(report["user_id"], self.user.id)
        self.assertEqual(report["employee_name"], "Rita Shrestha")
        self.assertEqual(report["department"], "Technology")
        self.assertEqual(report["total_expenses"], "450.00")
        self.assertEqual(report["expense_count"], 3)
        self.assertEqual(report["top_category"], "Software")

    def test_employee_summary_approval_status_totals(self):
        response = self.client.get(reverse("employee-summary-report"), {"department": self.department.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.data["data"][0]
        self.assertEqual(report["approved_amount"], "250.00")
        self.assertEqual(report["pending_amount"], "150.00")
        self.assertEqual(report["rejected_amount"], "50.00")

    def test_employee_summary_optional_filters(self):
        response = self.client.get(
            reverse("employee-summary-report"),
            {
                "department": self.department.id,
                "date_from": "2026-03-01",
                "date_to": "2026-03-31",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.data["data"][0]
        self.assertEqual(report["total_expenses"], "50.00")
        self.assertEqual(report["expense_count"], 1)
        self.assertEqual(report["rejected_amount"], "50.00")
        self.assertEqual(report["top_category"], "Travel")

    def test_employee_summary_empty_result(self):
        response = self.client.get(
            reverse("employee-summary-report"),
            {"department": self.other_department.id, "date_from": "2026-03-01"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"], [])
