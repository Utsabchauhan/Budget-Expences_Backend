from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response

from approvals.serializers import ApprovalSerializer
from approvals.services import ApprovalService
from budgets.serializers import BudgetSerializer
from budgets.services import BudgetService
from categories.serializers import CategorySerializer
from categories.services import CategoryService
from departments.serializers import DepartmentSerializer
from departments.services import DepartmentService
from expenses.serializers import ExpenseSerializer
from expenses.services import ExpenseService
from income.serializers import IncomeSerializer
from income.services import IncomeService
from reports.serializers import BudgetSummarySerializer
from reports.services import ExpenseReportService, MonthlyBudgetSummaryService

from .permissions import RolePermission


class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


def success_response(data=None, status_code=status.HTTP_200_OK):
    payload = {"success": True}
    if status_code != status.HTTP_204_NO_CONTENT:
        payload["data"] = data
    return Response(payload if status_code != status.HTTP_204_NO_CONTENT else None, status=status_code)


def error_response(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response(
        {
            "success": False,
            "message": message,
            "errors": errors,
        },
        status=status_code,
    )


def format_error_detail(error):
    if hasattr(error, "detail"):
        return error.detail
    if hasattr(error, "message_dict"):
        return error.message_dict
    if hasattr(error, "messages"):
        return error.messages
    return None


class ServiceCRUDViewSet(viewsets.ViewSet):
    serializer_class = None
    service_class = None
    filter_fields = []
    pagination_class = StandardPagination
    permission_classes = [RolePermission]

    def list(self, request):
        queryset = self.filter_queryset(self.service_class.list_all(), request)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        serializer = self.serializer_class(page, many=True)
        return success_response(
            {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            }
        )

    def create(self, request):
        try:
            instance = self.service_class.create(request.data)
        except (DRFValidationError, DjangoValidationError) as error:
            return error_response("Validation failed.", format_error_detail(error))
        except IntegrityError:
            return error_response(
                "A database constraint prevented this operation.",
                status_code=status.HTTP_409_CONFLICT,
            )
        serializer = self.serializer_class(instance)
        return success_response(serializer.data, status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        try:
            instance = self.service_class.get_by_id(pk)
        except ObjectDoesNotExist:
            return error_response("Resource not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(instance)
        return success_response(serializer.data)

    def update(self, request, pk=None):
        return self._update(request, pk)

    def partial_update(self, request, pk=None):
        return self._update(request, pk)

    def destroy(self, request, pk=None):
        try:
            self.service_class.delete(pk)
        except ObjectDoesNotExist:
            return error_response("Resource not found.", status_code=status.HTTP_404_NOT_FOUND)
        except (DjangoValidationError, ProtectedError):
            return error_response(
                "Resource cannot be deleted because related records depend on it.",
                status_code=status.HTTP_409_CONFLICT,
            )
        except IntegrityError:
            return error_response(
                "A database constraint prevented this operation.",
                status_code=status.HTTP_409_CONFLICT,
            )
        return success_response(status_code=status.HTTP_204_NO_CONTENT)

    def _update(self, request, pk):
        try:
            instance = self.service_class.update(pk, request.data)
        except ObjectDoesNotExist:
            return error_response("Resource not found.", status_code=status.HTTP_404_NOT_FOUND)
        except (DRFValidationError, DjangoValidationError) as error:
            return error_response("Validation failed.", format_error_detail(error))
        except IntegrityError:
            return error_response(
                "A database constraint prevented this operation.",
                status_code=status.HTTP_409_CONFLICT,
            )
        serializer = self.serializer_class(instance)
        return success_response(serializer.data)

    def filter_queryset(self, queryset, request):
        filters = {}
        for field in self.filter_fields:
            value = request.query_params.get(field)
            if value:
                filters[field] = value
        if filters:
            queryset = queryset.filter(**filters)
        return queryset


class DepartmentViewSet(ServiceCRUDViewSet):
    serializer_class = DepartmentSerializer
    service_class = DepartmentService
    filter_fields = ["status"]


class CategoryViewSet(ServiceCRUDViewSet):
    serializer_class = CategorySerializer
    service_class = CategoryService
    filter_fields = ["status"]


class BudgetViewSet(ServiceCRUDViewSet):
    serializer_class = BudgetSerializer
    service_class = BudgetService
    filter_fields = ["status", "department", "category"]


class ExpenseViewSet(ServiceCRUDViewSet):
    serializer_class = ExpenseSerializer
    service_class = ExpenseService
    filter_fields = ["status", "department", "category"]


class IncomeViewSet(ServiceCRUDViewSet):
    serializer_class = IncomeSerializer
    service_class = IncomeService
    filter_fields = ["status", "department", "category"]


class ApprovalViewSet(ServiceCRUDViewSet):
    serializer_class = ApprovalSerializer
    service_class = ApprovalService
    filter_fields = ["status"]


class ReportAPIView(APIView):
    report_method = None
    permission_classes = [RolePermission]

    def get(self, request, entity_id):
        try:
            data = self.report_method(entity_id)
        except ObjectDoesNotExist:
            return error_response("Resource not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data)


class EmployeeExpensesReportView(ReportAPIView):
    report_method = staticmethod(ExpenseReportService.get_employee_expenses)


class DepartmentExpensesReportView(ReportAPIView):
    report_method = staticmethod(ExpenseReportService.get_department_expenses)


class CategoryExpensesReportView(ReportAPIView):
    report_method = staticmethod(ExpenseReportService.get_category_expenses)


class BudgetUtilizationReportView(APIView):
    permission_classes = [RolePermission]

    def get(self, request):
        data = ExpenseReportService.get_budget_utilization(
            department=request.query_params.get("department"),
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
        )
        return success_response(data)


class EmployeeSummaryReportView(APIView):
    permission_classes = [RolePermission]

    def get(self, request):
        data = ExpenseReportService.get_employee_summary(
            department=request.query_params.get("department"),
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
        )
        return success_response(data)


class MonthlySummaryGenerateView(APIView):
    permission_classes = [RolePermission]

    def post(self, request):
        try:
            summaries = MonthlyBudgetSummaryService.generate_async(
                request.data.get("month"),
                request.data.get("year"),
            )
        except (DRFValidationError, DjangoValidationError) as error:
            return error_response("Validation failed.", format_error_detail(error))

        return success_response(
            {
                "message": "Monthly summary generation started.",
                "summary_ids": [summary.id for summary in summaries],
            },
            status.HTTP_202_ACCEPTED,
        )


class MonthlySummaryListView(APIView):
    permission_classes = [RolePermission]

    def get(self, request):
        try:
            queryset = MonthlyBudgetSummaryService.list_all(
                {
                    "month": request.query_params.get("month"),
                    "year": request.query_params.get("year"),
                    "department": request.query_params.get("department"),
                }
            )
        except (DRFValidationError, DjangoValidationError) as error:
            return error_response("Validation failed.", format_error_detail(error))

        serializer = BudgetSummarySerializer(queryset, many=True)
        return success_response(serializer.data)


class MonthlySummaryDetailView(APIView):
    permission_classes = [RolePermission]

    def get(self, request, pk):
        try:
            summary = MonthlyBudgetSummaryService.get_by_id(pk)
        except ObjectDoesNotExist:
            return error_response("Resource not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = BudgetSummarySerializer(summary)
        return success_response(serializer.data)
