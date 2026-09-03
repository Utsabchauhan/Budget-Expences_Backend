from django.contrib import admin

from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "status", "created_at")
    list_filter = ("type", "status")
    search_fields = ("name",)
