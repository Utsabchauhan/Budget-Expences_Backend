from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "type",
            "description",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
        validators = []

    def validate(self, attrs):
        name = attrs.get("name", getattr(self.instance, "name", None))
        category_type = attrs.get("type", getattr(self.instance, "type", None))
        if name and category_type:
            duplicate = Category.objects.filter(name__iexact=name, type=category_type)
            if self.instance:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise serializers.ValidationError(
                    {"name": "A category with this name and type already exists."}
                )
        return attrs
