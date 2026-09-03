from rest_framework import serializers

from .models import BudgetSummary


class BudgetSummarySerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = BudgetSummary
        fields = [
            "id",
            "department",
            "department_name",
            "month",
            "year",
            "total_budget",
            "total_expense",
            "total_income",
            "remaining_budget",
            "utilization_percentage",
            "status",
            "generated_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "department_name",
            "total_budget",
            "total_expense",
            "total_income",
            "remaining_budget",
            "utilization_percentage",
            "generated_at",
            "created_at",
            "updated_at",
        ]
