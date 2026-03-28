from django.db import models
from django.conf import settings
from core.models import BaseModel


class Category(BaseModel):
    class CategoryType(models.TextChoices):
        INCOME  = 'income',  'Income'
        EXPENSE = 'expense', 'Expense'


    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='custom_categories'
    )
    name          = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=CategoryType.choices)
    is_preset     = models.BooleanField(default=False)

    def __str__(self):
        label = "Preset" if self.is_preset else self.user.username
        return f"[{label}] {self.name} ({self.category_type})"


class Income(BaseModel):
    user     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='incomes'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    description = models.CharField(max_length=200)
    amount      = models.DecimalField(max_digits=12, decimal_places=2)
    date        = models.DateField()
    notes       = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} | +{self.amount} | {self.date}"


class Expense(BaseModel):
    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    category    = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    description = models.CharField(max_length=200)
    amount      = models.DecimalField(max_digits=12, decimal_places=2)
    date        = models.DateField()
    notes       = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} | -{self.amount} | {self.date}"