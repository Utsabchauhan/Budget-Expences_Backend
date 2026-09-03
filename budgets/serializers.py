from decimal import Decimal

from rest_framework import serializers

from categories.models import Category
from departments.serializers import user_display_name

from .models import Budget


class BudgetSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    created_by_name = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        model = Budget
        fields = [
            "id",
            "name",
            "department",
            "department_name",
            "category",
            "category_name",
            "amount",
            "start_date",
            "end_date",
            "description",
            "status",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["department_name", "category_name", "created_by_name", "created_at", "updated_at"]

    def get_created_by_name(self, obj: Budget) -> str:
        return user_display_name(obj.created_by)

    def validate_amount(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        category = attrs.get("category", getattr(self.instance, "category", None))

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "Budget end date cannot be before start date."}
            )
        if category and category.type != Category.Type.EXPENSE:
            raise serializers.ValidationError(
                {"category": "Budget category must be of type EXPENSE."}
            )
        return attrs
