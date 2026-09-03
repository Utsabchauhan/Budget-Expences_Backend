from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Department


def user_display_name(user: get_user_model()) -> str:
    full_name = user.get_full_name()
    return full_name or user.get_username()


class DepartmentSerializer(serializers.ModelSerializer):
    manager_name = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "code",
            "manager",
            "manager_name",
            "description",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "manager_name"]

    def get_manager_name(self, obj: Department) -> str | None:
        if not obj.manager:
            return None
        return user_display_name(obj.manager)
