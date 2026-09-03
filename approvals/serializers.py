from rest_framework import serializers

from departments.serializers import user_display_name

from .models import Approval


class ApprovalSerializer(serializers.ModelSerializer):
    expense_number = serializers.CharField(source="expense.expense_number", read_only=True)
    approver_name = serializers.SerializerMethodField()

    class Meta:
        model = Approval
        fields = [
            "id",
            "expense",
            "expense_number",
            "approver",
            "approver_name",
            "status",
            "comment",
            "decision_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["expense_number", "approver_name", "created_at", "updated_at"]

    def get_approver_name(self, obj: Approval) -> str:
        return user_display_name(obj.approver)
