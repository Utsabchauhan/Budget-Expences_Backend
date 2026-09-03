from decimal import Decimal

from rest_framework import serializers

from categories.models import Category
from departments.serializers import user_display_name

from .models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source="department.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    budget_name = serializers.CharField(source="budget.name", read_only=True)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        model = Expense
        fields = [
            "id",
            "expense_number",
            "user",
            "user_name",
            "department",
            "department_name",
            "category",
            "category_name",
            "budget",
            "budget_name",
            "title",
            "amount",
            "expense_date",
            "description",
            "payment_method",
            "reference_number",
            "receipt",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user_name", "department_name", "category_name", "budget_name", "created_at", "updated_at"]

    def get_user_name(self, obj: Expense) -> str:
        return user_display_name(obj.user)

    def validate_amount(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate(self, attrs):
        department = attrs.get("department", getattr(self.instance, "department", None))
        category = attrs.get("category", getattr(self.instance, "category", None))
        budget = attrs.get("budget", getattr(self.instance, "budget", None))

        if category and category.type != Category.Type.EXPENSE:
            raise serializers.ValidationError(
                {"category": "Expense category must be of type EXPENSE."}
            )
        if budget and department and budget.department_id != department.id:
            raise serializers.ValidationError(
                {"budget": "Budget must belong to the selected department."}
            )
        if budget and category and budget.category_id != category.id:
            raise serializers.ValidationError(
                {"budget": "Budget must use the selected expense category."}
            )
        return attrs
