from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from approvals.models import Approval

from .models import Expense
from .serializers import ExpenseSerializer


class ExpenseService:
    @staticmethod
    def create(data):
        serializer = ExpenseSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        expense = Expense(**serializer.validated_data)
        expense.full_clean()
        expense.save()
        return expense

    @staticmethod
    def update(expense_id, data):
        expense = ExpenseService.get_by_id(expense_id)
        serializer = ExpenseSerializer(expense, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(expense, field, value)
        expense.full_clean()
        expense.save()
        return expense

    @staticmethod
    def delete(expense_id):
        expense = ExpenseService.get_by_id(expense_id)
        if expense.approvals.exists():
            raise ValidationError("Cannot delete an expense with related approvals.")
        expense.delete()

    @staticmethod
    def get_by_id(expense_id):
        return Expense.objects.get(pk=expense_id)

    @staticmethod
    def list_all():
        return Expense.objects.select_related("user", "department", "category", "budget").all()

    @staticmethod
    @transaction.atomic
    def submit(expense_id):
        expense = ExpenseService.get_by_id(expense_id)
        expense.status = Expense.Status.PENDING
        expense.full_clean()
        expense.save(update_fields=["status", "updated_at"])
        return expense

    @staticmethod
    @transaction.atomic
    def approve(expense_id):
        expense = ExpenseService.get_by_id(expense_id)
        expense.status = Expense.Status.APPROVED
        expense.full_clean()
        expense.save(update_fields=["status", "updated_at"])
        expense.approvals.filter(
            status__in=[Approval.Status.PENDING, Approval.Status.REJECTED],
        ).update(status=Approval.Status.APPROVED, decision_date=timezone.now())
        return expense

    @staticmethod
    @transaction.atomic
    def reject(expense_id):
        expense = ExpenseService.get_by_id(expense_id)
        expense.status = Expense.Status.REJECTED
        expense.full_clean()
        expense.save(update_fields=["status", "updated_at"])
        expense.approvals.filter(
            status__in=[Approval.Status.PENDING, Approval.Status.APPROVED],
        ).update(status=Approval.Status.REJECTED, decision_date=timezone.now())
        return expense
