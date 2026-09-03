from .models import Income
from .serializers import IncomeSerializer


class IncomeService:
    @staticmethod
    def create(data):
        serializer = IncomeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        income = Income(**serializer.validated_data)
        income.full_clean()
        income.save()
        return income

    @staticmethod
    def update(income_id, data):
        income = IncomeService.get_by_id(income_id)
        serializer = IncomeSerializer(income, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(income, field, value)
        income.full_clean()
        income.save()
        return income

    @staticmethod
    def delete(income_id):
        income = IncomeService.get_by_id(income_id)
        income.delete()

    @staticmethod
    def get_by_id(income_id):
        return Income.objects.get(pk=income_id)

    @staticmethod
    def list_all():
        return Income.objects.select_related("user", "department", "category").all()
