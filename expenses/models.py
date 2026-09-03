from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from budgets.models import Budget
from categories.models import Category
from departments.models import Department


class Expense(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "CASH", "Cash"
        BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"
        CARD = "CARD", "Card"
        DIGITAL_WALLET = "DIGITAL_WALLET", "Digital Wallet"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    expense_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(r"^EXP-\d{6}$", "Use the format EXP-000001.")],
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    budget = models.ForeignKey(
        Budget,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
    )
    title = models.CharField(max_length=180)
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    expense_date = models.DateField(db_index=True)
    description = models.TextField(blank=True)
    payment_method = models.CharField(max_length=30, choices=PaymentMethod.choices)
    reference_number = models.CharField(max_length=80, blank=True)
    receipt = models.FileField(upload_to="receipts/expenses/", blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-expense_date", "-created_at"]
        indexes = [
            models.Index(fields=["department", "expense_date"]),
            models.Index(fields=["category", "expense_date"]),
            models.Index(fields=["status", "expense_date"]),
        ]

    def clean(self) -> None:
        if self.category_id and self.category.type != Category.Type.EXPENSE:
            raise ValidationError({"category": "Expense category must be an expense category."})
        if self.budget_id and self.budget.department_id != self.department_id:
            raise ValidationError({"budget": "Budget must belong to the same department as the expense."})

    def __str__(self) -> str:
        return f"{self.expense_number} - {self.title}"
