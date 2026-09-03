from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from approvals.models import Approval
from approvals.services import ApprovalService
from budgets.models import Budget
from budgets.services import BudgetService
from categories.models import Category
from categories.services import CategoryService
from departments.models import Department
from expenses.models import Expense
from expenses.services import ExpenseService
from income.models import Income
from income.services import IncomeService


class ServiceTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="requester", password="test-pass")
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
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            created_by=self.user,
        )

    def expense_data(self, expense_number="EXP-000001", amount=Decimal("250.00")):
        return {
            "expense_number": expense_number,
            "user": self.user.id,
            "department": self.department.id,
            "category": self.expense_category.id,
            "budget": self.budget.id,
            "title": "IDE subscription",
            "amount": amount,
            "expense_date": date(2026, 2, 1),
            "payment_method": Expense.PaymentMethod.CARD,
        }

    def test_create_expense(self):
        expense = ExpenseService.create(self.expense_data())

        self.assertEqual(expense.expense_number, "EXP-000001")
        self.assertEqual(expense.amount, Decimal("250.00"))
        self.assertEqual(expense.status, Expense.Status.DRAFT)

    def test_approve_expense_via_approval_service(self):
        expense = ExpenseService.create(self.expense_data())
        approval = ApprovalService.create(
            {
                "expense": expense.id,
                "approver": self.approver.id,
            }
        )

        ApprovalService.approve(approval.id, comment="Looks good.")
        approval.refresh_from_db()
        expense.refresh_from_db()

        self.assertEqual(approval.status, Approval.Status.APPROVED)
        self.assertEqual(approval.comment, "Looks good.")
        self.assertIsNotNone(approval.decision_date)
        self.assertEqual(expense.status, Expense.Status.APPROVED)

    def test_reject_expense_via_approval_service(self):
        expense = ExpenseService.create(self.expense_data())
        approval = ApprovalService.create(
            {
                "expense": expense.id,
                "approver": self.approver.id,
            }
        )

        ApprovalService.reject(approval.id, comment="Need receipt.")
        approval.refresh_from_db()
        expense.refresh_from_db()

        self.assertEqual(approval.status, Approval.Status.REJECTED)
        self.assertEqual(approval.comment, "Need receipt.")
        self.assertIsNotNone(approval.decision_date)
        self.assertEqual(expense.status, Expense.Status.REJECTED)

    def test_budget_remaining_and_utilization_use_approved_expenses(self):
        approved_expense = ExpenseService.create(self.expense_data(amount=Decimal("250.00")))
        ExpenseService.create(self.expense_data("EXP-000002", amount=Decimal("100.00")))
        ExpenseService.approve(approved_expense.id)

        self.assertEqual(BudgetService.calculate_spent(self.budget.id), Decimal("250.00"))
        self.assertEqual(BudgetService.calculate_remaining(self.budget.id), Decimal("750.00"))
        self.assertEqual(BudgetService.calculate_utilization(self.budget.id), Decimal("25.00"))

    def test_income_create(self):
        income = IncomeService.create(
            {
                "income_number": "INC-000001",
                "user": self.user.id,
                "department": self.department.id,
                "category": self.income_category.id,
                "source": "Product sales",
                "amount": Decimal("1500.00"),
                "income_date": date(2026, 2, 3),
            }
        )

        self.assertEqual(income.income_number, "INC-000001")
        self.assertEqual(income.amount, Decimal("1500.00"))
        self.assertEqual(income.status, Income.Status.DRAFT)

    def test_protected_delete_behavior(self):
        ExpenseService.create(self.expense_data())

        with self.assertRaises(ValidationError):
            CategoryService.delete(self.expense_category.id)
