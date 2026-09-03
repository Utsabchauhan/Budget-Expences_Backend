from decimal import Decimal

from rest_framework import serializers

from categories.models import Category
from departments.serializers import user_display_name

from .models import Income


class IncomeSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source="department.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        model = Income
        fields = [
            "id",
            "income_number",
            "user",
            "user_name",
            "department",
            "department_name",
            "category",
            "category_name",
            "source",
            "amount",
            "income_date",
            "description",
            "reference_number",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user_name", "department_name", "category_name", "created_at", "updated_at"]

    def get_user_name(self, obj: Income) -> str:
        return user_display_name(obj.user)

    def validate_amount(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate(self, attrs):
        category = attrs.get("category", getattr(self.instance, "category", None))
        if category and category.type != Category.Type.INCOME:
            raise serializers.ValidationError(
                {"category": "Income category must be of type INCOME."}
            )
        return attrs
