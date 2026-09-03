from django.db import transaction
from django.utils import timezone

from expenses.models import Expense

from .models import Approval
from .serializers import ApprovalSerializer


class ApprovalService:
    @staticmethod
    @transaction.atomic
    def create(data):
        serializer = ApprovalSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        approval = Approval(**serializer.validated_data)
        if approval.status != Approval.Status.PENDING:
            approval.decision_date = timezone.now()
        approval.full_clean()
        approval.save()
        ApprovalService._sync_expense_status(approval)
        return approval

    @staticmethod
    @transaction.atomic
    def update(approval_id, data):
        approval = ApprovalService.get_by_id(approval_id)
        serializer = ApprovalSerializer(approval, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        previous_status = approval.status
        for field, value in serializer.validated_data.items():
            setattr(approval, field, value)
        if approval.status != Approval.Status.PENDING and approval.status != previous_status:
            approval.decision_date = timezone.now()
        approval.full_clean()
        approval.save()
        ApprovalService._sync_expense_status(approval)
        return approval

    @staticmethod
    def delete(approval_id):
        approval = ApprovalService.get_by_id(approval_id)
        approval.delete()

    @staticmethod
    @transaction.atomic
    def approve(approval_id, comment=None):
        approval = ApprovalService.get_by_id(approval_id)
        approval.status = Approval.Status.APPROVED
        if comment is not None:
            approval.comment = comment
        approval.decision_date = timezone.now()
        approval.full_clean()
        approval.save(update_fields=["status", "comment", "decision_date", "updated_at"])
        ApprovalService._sync_expense_status(approval)
        return approval

    @staticmethod
    @transaction.atomic
    def reject(approval_id, comment=None):
        approval = ApprovalService.get_by_id(approval_id)
        approval.status = Approval.Status.REJECTED
        if comment is not None:
            approval.comment = comment
        approval.decision_date = timezone.now()
        approval.full_clean()
        approval.save(update_fields=["status", "comment", "decision_date", "updated_at"])
        ApprovalService._sync_expense_status(approval)
        return approval

    @staticmethod
    def get_by_id(approval_id):
        return Approval.objects.select_related("expense", "approver").get(pk=approval_id)

    @staticmethod
    def list_all():
        return Approval.objects.select_related("expense", "approver").all()

    @staticmethod
    def _sync_expense_status(approval):
        status_map = {
            Approval.Status.PENDING: Expense.Status.PENDING,
            Approval.Status.APPROVED: Expense.Status.APPROVED,
            Approval.Status.REJECTED: Expense.Status.REJECTED,
        }
        expense = approval.expense
        expense.status = status_map[approval.status]
        expense.full_clean()
        expense.save(update_fields=["status", "updated_at"])
