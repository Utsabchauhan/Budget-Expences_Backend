from django.core.exceptions import ValidationError

from .models import Department
from .serializers import DepartmentSerializer


class DepartmentService:
    @staticmethod
    def create(data):
        serializer = DepartmentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        department = Department(**serializer.validated_data)
        department.full_clean()
        department.save()
        return department

    @staticmethod
    def update(department_id, data):
        department = DepartmentService.get_by_id(department_id)
        serializer = DepartmentSerializer(department, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(department, field, value)
        department.full_clean()
        department.save()
        return department

    @staticmethod
    def delete(department_id):
        department = DepartmentService.get_by_id(department_id)
        if (
            department.budgets.exists()
            or department.expenses.exists()
            or department.income_records.exists()
        ):
            raise ValidationError("Cannot delete a department with related finance records.")
        department.delete()

    @staticmethod
    def get_by_id(department_id):
        return Department.objects.get(pk=department_id)

    @staticmethod
    def list_all():
        return Department.objects.all()
