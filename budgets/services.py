from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Sum

from expenses.models import Expense

from .models import Budget
from .serializers import BudgetSerializer


class BudgetService:
    @staticmethod
    def create(data):
        serializer = BudgetSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        budget = Budget(**serializer.validated_data)
        budget.full_clean()
        budget.save()
        return budget

    @staticmethod
    def update(budget_id, data):
        budget = BudgetService.get_by_id(budget_id)
        serializer = BudgetSerializer(budget, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(budget, field, value)
        budget.full_clean()
        budget.save()
        return budget

    @staticmethod
    def delete(budget_id):
        budget = BudgetService.get_by_id(budget_id)
        if budget.expenses.exists():
            raise ValidationError("Cannot delete a budget with related expenses.")
        budget.delete()

    @staticmethod
    def get_by_id(budget_id):
        return Budget.objects.get(pk=budget_id)

    @staticmethod
    def list_all():
        return Budget.objects.select_related("department", "category", "created_by").all()

    @staticmethod
    def calculate_spent(budget_id):
        spent = Expense.objects.filter(
            budget_id=budget_id,
            status=Expense.Status.APPROVED,
        ).aggregate(total=Sum("amount"))["total"]
        return spent or Decimal("0.00")

    @staticmethod
    def calculate_remaining(budget_id):
        budget = BudgetService.get_by_id(budget_id)
        return budget.amount - BudgetService.calculate_spent(budget_id)

    @staticmethod
    def calculate_utilization(budget_id):
        budget = BudgetService.get_by_id(budget_id)
        spent = BudgetService.calculate_spent(budget_id)
        if budget.amount == Decimal("0.00"):
            return Decimal("0.00")
        return (spent / budget.amount * Decimal("100")).quantize(Decimal("0.01"))
