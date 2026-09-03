import calendar
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db import close_old_connections
from django.db.models import Count, DecimalField, Max, Min, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from approvals.models import Approval
from budgets.models import Budget
from categories.models import Category
from departments.models import Department
from departments.serializers import user_display_name
from expenses.models import Expense
from income.models import Income

from .models import BudgetSummary


summary_executor = ThreadPoolExecutor(max_workers=2)


class ExpenseReportService:
    @staticmethod
    def get_employee_expenses(user_id):
        user_model = get_user_model()
        user_model.objects.get(pk=user_id)
        expenses = ExpenseReportService._base_queryset().filter(user_id=user_id)
        return [
            {
                "expense_number": expense.expense_number,
                "title": expense.title,
                "amount": str(expense.amount),
                "date": expense.expense_date.isoformat(),
                "category": expense.category.name,
                "department": expense.department.name,
                "status": expense.status,
            }
            for expense in expenses
        ]

    @staticmethod
    def get_department_expenses(department_id):
        Department.objects.get(pk=department_id)
        expenses = ExpenseReportService._base_queryset().filter(department_id=department_id)
        return [
            {
                "expense_number": expense.expense_number,
                "employee": user_display_name(expense.user),
                "category": expense.category.name,
                "amount": str(expense.amount),
                "date": expense.expense_date.isoformat(),
                "status": expense.status,
            }
            for expense in expenses
        ]

    @staticmethod
    def get_category_expenses(category_id):
        Category.objects.get(pk=category_id)
        expenses = ExpenseReportService._base_queryset().filter(category_id=category_id)
        return [
            {
                "expense_number": expense.expense_number,
                "employee": user_display_name(expense.user),
                "department": expense.department.name,
                "amount": str(expense.amount),
                "date": expense.expense_date.isoformat(),
                "status": expense.status,
            }
            for expense in expenses
        ]

    @staticmethod
    def _base_queryset():
        return Expense.objects.select_related("user", "department", "category").all()

    @staticmethod
    def get_budget_utilization(department=None, date_from=None, date_to=None):
        expense_sum = Expense.objects.filter(budget_id=OuterRef("pk"))
        if date_from:
            expense_sum = expense_sum.filter(expense_date__gte=date_from)
        if date_to:
            expense_sum = expense_sum.filter(expense_date__lte=date_to)
        expense_sum = (
            expense_sum.values("budget_id")
            .annotate(total=Sum("amount"))
            .values("total")[:1]
        )

        budgets = Budget.objects.select_related("department", "category").annotate(
            total_expense=Coalesce(
                Subquery(expense_sum, output_field=DecimalField(max_digits=14, decimal_places=2)),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
        if department:
            budgets = budgets.filter(department_id=department)

        return [
            {
                "department": budget.department.name,
                "category": budget.category.name,
                "allocated_budget": ExpenseReportService._format_money(budget.amount),
                "total_expense": ExpenseReportService._format_money(budget.total_expense),
                "remaining_budget": ExpenseReportService._format_money(budget.amount - budget.total_expense),
                "utilization_percentage": str(
                    ExpenseReportService._calculate_utilization(budget.total_expense, budget.amount)
                ),
                "status": ExpenseReportService._budget_status(budget.total_expense, budget.amount),
            }
            for budget in budgets
        ]

    @staticmethod
    def get_employee_summary(department=None, date_from=None, date_to=None):
        user_model = get_user_model()
        expense_filter = Q(expenses__isnull=False)
        top_category_filter = Q(user_id=OuterRef("pk"))
        if department:
            expense_filter &= Q(expenses__department_id=department)
            top_category_filter &= Q(department_id=department)
        if date_from:
            expense_filter &= Q(expenses__expense_date__gte=date_from)
            top_category_filter &= Q(expense_date__gte=date_from)
        if date_to:
            expense_filter &= Q(expenses__expense_date__lte=date_to)
            top_category_filter &= Q(expense_date__lte=date_to)

        top_category = (
            Expense.objects.filter(top_category_filter)
            .values("category__name")
            .annotate(category_total=Sum("amount"))
            .order_by("-category_total", "category__name")
            .values("category__name")[:1]
        )
        users = (
            user_model.objects.filter(expenses__isnull=False)
            .annotate(
                total_expenses=Coalesce(
                    Sum("expenses__amount", filter=expense_filter),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
                expense_count=Count("expenses", filter=expense_filter, distinct=True),
                approved_amount=Coalesce(
                    Sum(
                        "expenses__amount",
                        filter=expense_filter & Q(expenses__approvals__status=Approval.Status.APPROVED),
                    ),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
                pending_amount=Coalesce(
                    Sum(
                        "expenses__amount",
                        filter=expense_filter & Q(expenses__approvals__status=Approval.Status.PENDING),
                    ),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
                rejected_amount=Coalesce(
                    Sum(
                        "expenses__amount",
                        filter=expense_filter & Q(expenses__approvals__status=Approval.Status.REJECTED),
                    ),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
                first_department=Min("expenses__department__name", filter=expense_filter),
                last_department=Max("expenses__department__name", filter=expense_filter),
                top_category=Subquery(top_category),
            )
            .filter(expense_count__gt=0)
            .order_by("username")
        )

        return [
            {
                "user_id": user.id,
                "employee_name": user_display_name(user),
                "department": (
                    user.first_department
                    if user.first_department == user.last_department
                    else "Multiple"
                ),
                "total_expenses": ExpenseReportService._format_money(user.total_expenses),
                "expense_count": user.expense_count,
                "approved_amount": ExpenseReportService._format_money(user.approved_amount),
                "pending_amount": ExpenseReportService._format_money(user.pending_amount),
                "rejected_amount": ExpenseReportService._format_money(user.rejected_amount),
                "top_category": user.top_category,
            }
            for user in users
        ]

    @staticmethod
    def _calculate_utilization(total_expense, allocated_budget):
        if allocated_budget == 0:
            return Decimal("0.00")
        return (total_expense / allocated_budget * 100).quantize(Decimal("0.01"))

    @staticmethod
    def _budget_status(total_expense, allocated_budget):
        if allocated_budget and total_expense > allocated_budget:
            return "OVER_BUDGET"
        if allocated_budget and total_expense / allocated_budget >= 0.8:
            return "WARNING"
        return "NORMAL"

    @staticmethod
    def _format_money(value):
        return str(value.quantize(Decimal("0.01")))


class MonthlyBudgetSummaryService:
    @staticmethod
    def generate_async(month, year):
        month, year = MonthlyBudgetSummaryService.validate_month_year(month, year)
        with transaction.atomic():
            summaries = []
            for department in Department.objects.all():
                summary, _ = BudgetSummary.objects.update_or_create(
                    department=department,
                    month=month,
                    year=year,
                    defaults={
                        "status": BudgetSummary.Status.PENDING,
                        "total_budget": Decimal("0.00"),
                        "total_expense": Decimal("0.00"),
                        "total_income": Decimal("0.00"),
                        "remaining_budget": Decimal("0.00"),
                        "utilization_percentage": Decimal("0.00"),
                        "generated_at": None,
                    },
                )
                summaries.append(summary)

        summary_executor.submit(MonthlyBudgetSummaryService.calculate_monthly_summary, month, year)
        return summaries

    @staticmethod
    def calculate_monthly_summary(month, year):
        close_old_connections()
        try:
            month, year = MonthlyBudgetSummaryService.validate_month_year(month, year)
            month_start, month_end = MonthlyBudgetSummaryService.month_bounds(month, year)
            for summary in BudgetSummary.objects.select_related("department").filter(month=month, year=year):
                MonthlyBudgetSummaryService.calculate_department_summary(summary.id, month_start, month_end)
        finally:
            close_old_connections()

    @staticmethod
    def calculate_department_summary(summary_id, month_start, month_end):
        with transaction.atomic():
            summary = BudgetSummary.objects.select_for_update().select_related("department").get(pk=summary_id)
            summary.status = BudgetSummary.Status.PROCESSING
            summary.save(update_fields=["status", "updated_at"])

        try:
            department = summary.department
            total_budget = MonthlyBudgetSummaryService._sum_or_zero(
                Budget.objects.filter(
                    department=department,
                    start_date__lte=month_end,
                    end_date__gte=month_start,
                ).aggregate(total=Sum("amount"))["total"]
            )
            total_expense = MonthlyBudgetSummaryService._sum_or_zero(
                Expense.objects.filter(
                    department=department,
                    expense_date__gte=month_start,
                    expense_date__lte=month_end,
                ).aggregate(total=Sum("amount"))["total"]
            )
            total_income = MonthlyBudgetSummaryService._sum_or_zero(
                Income.objects.filter(
                    department=department,
                    income_date__gte=month_start,
                    income_date__lte=month_end,
                ).aggregate(total=Sum("amount"))["total"]
            )
            remaining_budget = total_budget - total_expense
            utilization_percentage = MonthlyBudgetSummaryService.calculate_utilization(
                total_expense,
                total_budget,
            )

            with transaction.atomic():
                summary = BudgetSummary.objects.select_for_update().get(pk=summary_id)
                summary.total_budget = total_budget
                summary.total_expense = total_expense
                summary.total_income = total_income
                summary.remaining_budget = remaining_budget
                summary.utilization_percentage = utilization_percentage
                summary.status = BudgetSummary.Status.COMPLETED
                summary.generated_at = timezone.now()
                summary.full_clean()
                summary.save()
        except Exception:
            with transaction.atomic():
                BudgetSummary.objects.filter(pk=summary_id).update(status=BudgetSummary.Status.FAILED)
            raise

    @staticmethod
    def list_all(filters=None):
        queryset = BudgetSummary.objects.select_related("department").all()
        filters = filters or {}
        if filters.get("month"):
            try:
                month = int(filters["month"])
            except (TypeError, ValueError):
                raise ValidationError({"month": "Month must be a valid integer."})
            if month < 1 or month > 12:
                raise ValidationError({"month": "Month must be between 1 and 12."})
            queryset = queryset.filter(month=month)
        if filters.get("year"):
            try:
                year = int(filters["year"])
            except (TypeError, ValueError):
                raise ValidationError({"year": "Year must be a valid integer."})
            if year < 1:
                raise ValidationError({"year": "Year must be greater than zero."})
            queryset = queryset.filter(year=year)
        if filters.get("department"):
            try:
                department = int(filters["department"])
            except (TypeError, ValueError):
                raise ValidationError({"department": "Department must be a valid integer."})
            queryset = queryset.filter(department_id=department)
        return queryset

    @staticmethod
    def get_by_id(summary_id):
        return BudgetSummary.objects.select_related("department").get(pk=summary_id)

    @staticmethod
    def validate_month_year(month, year):
        try:
            month = int(month)
            year = int(year)
        except (TypeError, ValueError):
            raise ValidationError({"month": "Month and year must be valid integers."})
        if month < 1 or month > 12:
            raise ValidationError({"month": "Month must be between 1 and 12."})
        if year < 1:
            raise ValidationError({"year": "Year must be greater than zero."})
        return month, year

    @staticmethod
    def month_bounds(month, year):
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, 1), date(year, month, last_day)

    @staticmethod
    def calculate_utilization(total_expense, total_budget):
        if total_budget == Decimal("0.00"):
            return Decimal("0.00")
        return (total_expense / total_budget * Decimal("100")).quantize(Decimal("0.01"))

    @staticmethod
    def _sum_or_zero(value):
        return value or Decimal("0.00")
