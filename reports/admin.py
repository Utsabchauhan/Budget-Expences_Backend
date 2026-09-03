from django.contrib import admin

from .models import BudgetSummary


@admin.register(BudgetSummary)
class BudgetSummaryAdmin(admin.ModelAdmin):
    list_display = ("department", "month", "year", "total_budget", "total_expense", "total_income", "status")
    list_filter = ("status", "year", "month", "department")
    search_fields = ("department__name",)
