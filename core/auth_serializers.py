from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import UserProfile


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is inactive.")
        attrs["user"] = user
        return attrs


class UserInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)
    full_name = serializers.CharField(allow_blank=True)
    role = serializers.CharField()
    department = serializers.DictField(allow_null=True)


def user_info(user):
    profile, _ = UserProfile.objects.select_related("department").get_or_create(user=user)
    department = None
    if profile.department:
        department = {
            "id": profile.department.id,
            "name": profile.department.name,
            "code": profile.department.code,
        }
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.get_full_name(),
        "role": profile.role,
        "department": department,
    }
