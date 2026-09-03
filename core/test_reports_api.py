from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from budgets.models import Budget
from categories.models import Category
from departments.models import Department
from expenses.models import Expense
from core.models import UserProfile


class ExpenseReportAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="requester",
            first_name="Rita",
            last_name="Shrestha",
            password="test-pass",
        )
        self.user.profile.role = UserProfile.Role.ADMIN
        self.user.profile.save(update_fields=["role", "updated_at"])
        self.client.force_authenticate(user=self.user)
        self.other_user = user_model.objects.create_user(username="other", password="test-pass")
        self.department = Department.objects.create(name="Technology", code="TECH")
        self.empty_department = Department.objects.create(name="Operations", code="OPS")
        self.category = Category.objects.create(name="Software", type=Category.Type.EXPENSE)
        self.other_category = Category.objects.create(name="Travel", type=Category.Type.EXPENSE)
        self.budget = Budget.objects.create(
            name="Software Budget",
            department=self.department,
            category=self.category,
            amount=Decimal("1000.00"),
            start_date="2026-01-01",
            end_date="2026-12-31",
            created_by=self.user,
        )
        self.expense = Expense.objects.create(
            expense_number="EXP-000001",
            user=self.user,
            department=self.department,
            category=self.category,
            budget=self.budget,
            title="IDE subscription",
            amount=Decimal("250.00"),
            expense_date="2026-02-01",
            payment_method=Expense.PaymentMethod.CARD,
            status=Expense.Status.APPROVED,
        )
        Expense.objects.create(
            expense_number="EXP-000002",
            user=self.other_user,
            department=self.department,
            category=self.other_category,
            title="Taxi fare",
            amount=Decimal("40.00"),
            expense_date="2026-02-02",
            payment_method=Expense.PaymentMethod.CASH,
            status=Expense.Status.PENDING,
        )

    def test_employee_expenses_query(self):
        response = self.client.get(reverse("employee-expenses-report", args=[self.user.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["data"]), 1)
        expense = response.data["data"][0]
        self.assertEqual(expense["expense_number"], "EXP-000001")
        self.assertEqual(expense["title"], "IDE subscription")
        self.assertEqual(expense["amount"], "250.00")
        self.assertEqual(expense["date"], "2026-02-01")
        self.assertEqual(expense["category"], "Software")
        self.assertEqual(expense["department"], "Technology")
        self.assertEqual(expense["status"], Expense.Status.APPROVED)

    def test_department_expenses_query(self):
        response = self.client.get(reverse("department-expenses-report", args=[self.department.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["data"]), 2)
        first_expense = response.data["data"][0]
        self.assertIn("expense_number", first_expense)
        self.assertIn("employee", first_expense)
        self.assertIn("category", first_expense)
        self.assertIn("amount", first_expense)
        self.assertIn("date", first_expense)
        self.assertIn("status", first_expense)

    def test_category_expenses_query(self):
        response = self.client.get(reverse("category-expenses-report", args=[self.category.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["data"]), 1)
        expense = response.data["data"][0]
        self.assertEqual(expense["expense_number"], "EXP-000001")
        self.assertEqual(expense["employee"], "Rita Shrestha")
        self.assertEqual(expense["department"], "Technology")
        self.assertEqual(expense["amount"], "250.00")
        self.assertEqual(expense["date"], "2026-02-01")
        self.assertEqual(expense["status"], Expense.Status.APPROVED)

    def test_invalid_entity_id_returns_404(self):
        response = self.client.get(reverse("employee-expenses-report", args=[999999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["message"], "Resource not found.")

    def test_valid_entity_with_no_expenses_returns_empty_list(self):
        response = self.client.get(reverse("department-expenses-report", args=[self.empty_department.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"], [])
