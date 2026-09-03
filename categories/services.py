from django.core.exceptions import ValidationError

from .models import Category
from .serializers import CategorySerializer


class CategoryService:
    @staticmethod
    def create(data):
        serializer = CategorySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        category = Category(**serializer.validated_data)
        category.full_clean()
        category.save()
        return category

    @staticmethod
    def update(category_id, data):
        category = CategoryService.get_by_id(category_id)
        serializer = CategorySerializer(category, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(category, field, value)
        category.full_clean()
        category.save()
        return category

    @staticmethod
    def delete(category_id):
        category = CategoryService.get_by_id(category_id)
        if (
            category.budgets.exists()
            or category.expenses.exists()
            or category.income_records.exists()
        ):
            raise ValidationError("Cannot delete a category with related finance records.")
        category.delete()

    @staticmethod
    def get_by_id(category_id):
        return Category.objects.get(pk=category_id)

    @staticmethod
    def list_all():
        return Category.objects.all()
