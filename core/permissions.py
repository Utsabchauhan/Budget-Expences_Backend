from rest_framework.permissions import BasePermission

from .models import UserProfile


class RolePermission(BasePermission):
    finance_basename = {"budget", "expense", "income", "approval"}
    employee_basename = {"expense"}
    finance_report_views = {
        "EmployeeExpensesReportView",
        "DepartmentExpensesReportView",
        "CategoryExpensesReportView",
        "BudgetUtilizationReportView",
        "EmployeeSummaryReportView",
        "MonthlySummaryGenerateView",
        "MonthlySummaryListView",
        "MonthlySummaryDetailView",
    }

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        role = self.get_role(request.user)
        if role == UserProfile.Role.ADMIN:
            return True

        basename = getattr(view, "basename", None)
        view_name = view.__class__.__name__

        if role == UserProfile.Role.FINANCE:
            return basename in self.finance_basename or view_name in self.finance_report_views

        if role == UserProfile.Role.EMPLOYEE:
            return basename in self.employee_basename

        return False

    def get_role(self, user):
        if user.is_superuser:
            return UserProfile.Role.ADMIN
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return profile.role
