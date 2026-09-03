from django.contrib import admin

from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("expense_number", "title", "user", "department", "category", "amount", "status", "expense_date")
    list_filter = ("status", "payment_method", "department", "category")
    search_fields = ("expense_number", "title", "reference_number", "user__username")
