from django.contrib import admin

from .models import Income


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ("income_number", "source", "user", "department", "category", "amount", "status", "income_date")
    list_filter = ("status", "department", "category")
    search_fields = ("income_number", "source", "reference_number", "user__username")
