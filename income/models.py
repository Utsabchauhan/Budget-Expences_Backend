from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from categories.models import Category
from departments.models import Department


class Income(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    income_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(r"^INC-\d{6}$", "Use the format INC-000001.")],
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="income_records",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="income_records",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="income_records",
    )
    source = models.CharField(max_length=180)
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    income_date = models.DateField(db_index=True)
    description = models.TextField(blank=True)
    reference_number = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-income_date", "-created_at"]
        indexes = [
            models.Index(fields=["department", "income_date"]),
            models.Index(fields=["category", "income_date"]),
            models.Index(fields=["status", "income_date"]),
        ]

    def clean(self) -> None:
        if self.category_id and self.category.type != Category.Type.INCOME:
            raise ValidationError({"category": "Income category must be an income category."})

    def __str__(self) -> str:
        return f"{self.income_number} - {self.source}"
