from django.contrib import admin

from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "manager", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "code", "manager__username")
