from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from departments.models import Department


class BudgetSummary(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="budget_summaries",
    )
    month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], db_index=True)
    year = models.PositiveIntegerField(db_index=True)
    total_budget = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total_expense = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total_income = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    remaining_budget = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    utilization_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-month", "department__name"]
        constraints = [
            models.UniqueConstraint(fields=["department", "month", "year"], name="uq_budget_summary_department_month_year"),
        ]
        indexes = [
            models.Index(fields=["department", "year", "month"]),
        ]

    def __str__(self) -> str:
        return f"{self.department} - {self.month:02d}/{self.year}"
