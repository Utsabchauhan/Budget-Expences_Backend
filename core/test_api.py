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
from income.models import Income
from core.models import UserProfile


class CRUDAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="requester", password="test-pass")
        self.user.profile.role = UserProfile.Role.ADMIN
        self.user.profile.save(update_fields=["role", "updated_at"])
        self.client.force_authenticate(user=self.user)
        self.approver = user_model.objects.create_user(username="approver", password="test-pass")
        self.department = Department.objects.create(name="Technology", code="TECH")
        self.expense_category = Category.objects.create(
            name="Software",
            type=Category.Type.EXPENSE,
        )
        self.income_category = Category.objects.create(
            name="Sales",
            type=Category.Type.INCOME,
        )
        self.budget = Budget.objects.create(
            name="Software Budget",
            department=self.department,
            category=self.expense_category,
            amount=Decimal("1000.00"),
            start_date="2026-01-01",
            end_date="2026-12-31",
            created_by=self.user,
        )

    def expense_payload(self, expense_number="EXP-000001"):
        return {
            "expense_number": expense_number,
            "user": self.user.id,
            "department": self.department.id,
            "category": self.expense_category.id,
            "budget": self.budget.id,
            "title": "IDE subscription",
            "amount": "250.00",
            "expense_date": "2026-02-01",
            "payment_method": Expense.PaymentMethod.CARD,
        }

    def income_payload(self, income_number="INC-000001"):
        return {
            "income_number": income_number,
            "user": self.user.id,
            "department": self.department.id,
            "category": self.income_category.id,
            "source": "Product sales",
            "amount": "1500.00",
            "income_date": "2026-02-03",
        }

    def test_department_crud(self):
        response = self.client.post(
            reverse("department-list"),
            {"name": "Operations", "code": "OPS"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        department_id = response.data["data"]["id"]

        response = self.client.get(reverse("department-list"), {"status": Department.Status.ACTIVE})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["data"]["count"], 1)

        response = self.client.get(reverse("department-detail", args=[department_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["code"], "OPS")

        response = self.client.patch(
            reverse("department-detail", args=[department_id]),
            {"description": "Runs daily operations."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["description"], "Runs daily operations.")

        response = self.client.delete(reverse("department-detail", args=[department_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_category_crud(self):
        response = self.client.post(
            reverse("category-list"),
            {"name": "Travel", "type": Category.Type.EXPENSE},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        category_id = response.data["data"]["id"]

        response = self.client.get(reverse("category-list"), {"status": Category.Status.ACTIVE})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["data"]["count"], 1)

        response = self.client.get(reverse("category-detail", args=[category_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["name"], "Travel")

        response = self.client.patch(
            reverse("category-detail", args=[category_id]),
            {"description": "Employee travel costs."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["description"], "Employee travel costs.")

        response = self.client.delete(reverse("category-detail", args=[category_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_budget_crud(self):
        response = self.client.post(
            reverse("budget-list"),
            {
                "name": "Travel Budget",
                "department": self.department.id,
                "category": self.expense_category.id,
                "amount": "5000.00",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "created_by": self.user.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        budget_id = response.data["data"]["id"]

        response = self.client.get(
            reverse("budget-list"),
            {"department": self.department.id, "category": self.expense_category.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["data"]["count"], 1)

        response = self.client.get(reverse("budget-detail", args=[budget_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["name"], "Travel Budget")

        response = self.client.patch(
            reverse("budget-detail", args=[budget_id]),
            {"amount": "6000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["amount"], "6000.00")

        response = self.client.delete(reverse("budget-detail", args=[budget_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_expense_crud(self):
        response = self.client.post(reverse("expense-list"), self.expense_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expense_id = response.data["data"]["id"]

        response = self.client.get(reverse("expense-list"), {"department": self.department.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["data"]["count"], 1)

        response = self.client.get(reverse("expense-detail", args=[expense_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["expense_number"], "EXP-000001")

        response = self.client.patch(
            reverse("expense-detail", args=[expense_id]),
            {"title": "Annual IDE subscription"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["title"], "Annual IDE subscription")

        response = self.client.delete(reverse("expense-detail", args=[expense_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_income_crud(self):
        response = self.client.post(reverse("income-list"), self.income_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        income_id = response.data["data"]["id"]

        response = self.client.get(reverse("income-list"), {"category": self.income_category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["data"]["count"], 1)

        response = self.client.get(reverse("income-detail", args=[income_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["income_number"], "INC-000001")

        response = self.client.patch(
            reverse("income-detail", args=[income_id]),
            {"source": "Product sales - online"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["source"], "Product sales - online")

        response = self.client.delete(reverse("income-detail", args=[income_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_approval_crud(self):
        expense = Expense.objects.create(
            expense_number="EXP-000010",
            user=self.user,
            department=self.department,
            category=self.expense_category,
            budget=self.budget,
            title="Database tool",
            amount=Decimal("75.00"),
            expense_date="2026-02-05",
            payment_method=Expense.PaymentMethod.CARD,
        )

        response = self.client.post(
            reverse("approval-list"),
            {"expense": expense.id, "approver": self.approver.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        approval_id = response.data["data"]["id"]

        response = self.client.get(reverse("approval-list"), {"status": Approval.Status.PENDING})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["data"]["count"], 1)

        response = self.client.get(reverse("approval-detail", args=[approval_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["expense"], expense.id)

        response = self.client.patch(
            reverse("approval-detail", args=[approval_id]),
            {"comment": "Please verify receipt."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["comment"], "Please verify receipt.")

        response = self.client.delete(reverse("approval-detail", args=[approval_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_validation_failure_returns_standard_error(self):
        response = self.client.post(
            reverse("budget-list"),
            {
                "name": "Invalid Budget",
                "department": self.department.id,
                "category": self.income_category.id,
                "amount": "1000.00",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "created_by": self.user.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["message"], "Validation failed.")
        self.assertIn("category", response.data["errors"])
