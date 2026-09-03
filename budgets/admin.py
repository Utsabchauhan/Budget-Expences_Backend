from django.contrib import admin

from .models import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "category", "amount", "status", "start_date", "end_date")
    list_filter = ("status", "department", "category")
    search_fields = ("name", "department__name", "category__name")
