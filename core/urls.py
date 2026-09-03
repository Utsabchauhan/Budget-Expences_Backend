from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .auth_views import LoginView, LogoutView, MeView, RefreshView
from .api import (
    ApprovalViewSet,
    BudgetViewSet,
    BudgetUtilizationReportView,
    CategoryExpensesReportView,
    CategoryViewSet,
    DepartmentViewSet,
    DepartmentExpensesReportView,
    EmployeeExpensesReportView,
    EmployeeSummaryReportView,
    ExpenseViewSet,
    IncomeViewSet,
    MonthlySummaryDetailView,
    MonthlySummaryGenerateView,
    MonthlySummaryListView,
)
from .views import health


router = DefaultRouter()
router.register("departments", DepartmentViewSet, basename="department")
router.register("categories", CategoryViewSet, basename="category")
router.register("budgets", BudgetViewSet, basename="budget")
router.register("expenses", ExpenseViewSet, basename="expense")
router.register("income", IncomeViewSet, basename="income")
router.register("approvals", ApprovalViewSet, basename="approval")

urlpatterns = [
    path("health/", health, name="health"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path(
        "reports/employee-expenses/<int:entity_id>/",
        EmployeeExpensesReportView.as_view(),
        name="employee-expenses-report",
    ),
    path(
        "reports/department-expenses/<int:entity_id>/",
        DepartmentExpensesReportView.as_view(),
        name="department-expenses-report",
    ),
    path(
        "reports/category-expenses/<int:entity_id>/",
        CategoryExpensesReportView.as_view(),
        name="category-expenses-report",
    ),
    path(
        "reports/budget-utilization/",
        BudgetUtilizationReportView.as_view(),
        name="budget-utilization-report",
    ),
    path(
        "reports/employee-summary/",
        EmployeeSummaryReportView.as_view(),
        name="employee-summary-report",
    ),
    path(
        "reports/monthly-summary/generate/",
        MonthlySummaryGenerateView.as_view(),
        name="monthly-summary-generate",
    ),
    path(
        "reports/monthly-summary/",
        MonthlySummaryListView.as_view(),
        name="monthly-summary-list",
    ),
    path(
        "reports/monthly-summary/<int:pk>/",
        MonthlySummaryDetailView.as_view(),
        name="monthly-summary-detail",
    ),
    path("", include(router.urls)),
]
