from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from rest_framework import serializers

from budgets.models import Budget
from budgets.serializers import BudgetSerializer
from categories.models import Category
from categories.serializers import CategorySerializer
from departments.models import Department
from departments.serializers import DepartmentSerializer
from expenses.serializers import ExpenseSerializer
from income.serializers import IncomeSerializer
from reports.serializers import BudgetSummarySerializer


class SerializerTests(SimpleTestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model(
            id=1,
            username="surajan",
            first_name="Surajan",
            last_name="Shrestha",
            email="admin@budgetflow.com",
        )
        self.department = Department(
            id=1,
            name="Technology",
            code="TECH",
            manager=self.user,
            status=Department.Status.ACTIVE,
        )
        self.other_department = Department(
            id=2,
            name="Finance",
            code="FIN",
            status=Department.Status.ACTIVE,
        )
        self.expense_category = Category(
            id=1,
            name="Software",
            type=Category.Type.EXPENSE,
            status=Category.Status.ACTIVE,
        )
        self.income_category = Category(
            id=2,
            name="Sales",
            type=Category.Type.INCOME,
            status=Category.Status.ACTIVE,
        )
        self.budget = Budget(
            id=1,
            name="Technology Software Budget",
            department=self.department,
            department_id=self.department.id,
            category=self.expense_category,
            category_id=self.expense_category.id,
            amount=Decimal("100000.00"),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            created_by=self.user,
            status=Budget.Status.ACTIVE,
        )

    def test_department_serialization_includes_manager_name(self):
        data = DepartmentSerializer(self.department).data

        self.assertEqual(data["name"], "Technology")
        self.assertEqual(data["manager"], self.user.id)
        self.assertEqual(data["manager_name"], "Surajan Shrestha")
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_category_duplicate_name_and_type_validation(self):
        queryset = Mock()
        queryset.exists.return_value = True

        with patch("categories.serializers.Category.objects.filter", return_value=queryset):
            serializer = CategorySerializer()

            with self.assertRaises(serializers.ValidationError) as context:
                serializer.validate({"name": "software", "type": Category.Type.EXPENSE})

        self.assertIn("A category with this name and type already exists.", context.exception.detail["name"])

    def test_budget_positive_amount_and_date_validation(self):
        serializer = BudgetSerializer()

        with self.assertRaises(serializers.ValidationError) as amount_error:
            serializer.validate_amount(Decimal("0.00"))

        with self.assertRaises(serializers.ValidationError) as date_error:
            serializer.validate(
                {
                    "start_date": date(2026, 12, 31),
                    "end_date": date(2026, 1, 1),
                    "category": self.expense_category,
                }
            )

        self.assertEqual(str(amount_error.exception.detail[0]), "Amount must be greater than zero.")
        self.assertIn("Budget end date cannot be before start date.", date_error.exception.detail["end_date"])

    def test_budget_requires_expense_category(self):
        serializer = BudgetSerializer()

        with self.assertRaises(serializers.ValidationError) as context:
            serializer.validate(
                {
                    "start_date": date(2026, 1, 1),
                    "end_date": date(2026, 12, 31),
                    "category": self.income_category,
                }
            )

        self.assertIn("Budget category must be of type EXPENSE.", context.exception.detail["category"])

    def test_expense_requires_expense_category(self):
        serializer = ExpenseSerializer()

        with self.assertRaises(serializers.ValidationError) as context:
            serializer.validate(
                {
                    "department": self.department,
                    "category": self.income_category,
                    "budget": None,
                }
            )

        self.assertIn("Expense category must be of type EXPENSE.", context.exception.detail["category"])

    def test_expense_budget_must_match_department_and_category(self):
        serializer = ExpenseSerializer()

        with self.assertRaises(serializers.ValidationError) as context:
            serializer.validate(
                {
                    "department": self.other_department,
                    "category": self.expense_category,
                    "budget": self.budget,
                }
            )

        self.assertIn("Budget must belong to the selected department.", context.exception.detail["budget"])

    def test_income_requires_income_category(self):
        serializer = IncomeSerializer()

        with self.assertRaises(serializers.ValidationError) as context:
            serializer.validate({"category": self.expense_category})

        self.assertIn("Income category must be of type INCOME.", context.exception.detail["category"])

    def test_budget_summary_calculated_fields_are_read_only(self):
        serializer = BudgetSummarySerializer()
        fields = serializer.get_fields()

        for field_name in [
            "total_budget",
            "total_expense",
            "total_income",
            "remaining_budget",
            "utilization_percentage",
            "generated_at",
        ]:
            self.assertTrue(fields[field_name].read_only)

        self.assertFalse(fields["department"].read_only)
        self.assertFalse(fields["month"].read_only)
        self.assertFalse(fields["year"].read_only)
