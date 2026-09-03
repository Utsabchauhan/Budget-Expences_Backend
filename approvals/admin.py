from django.contrib import admin

from .models import Approval


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ("expense", "approver", "status", "decision_date", "created_at")
    list_filter = ("status", "decision_date")
    search_fields = ("expense__expense_number", "approver__username", "comment")
