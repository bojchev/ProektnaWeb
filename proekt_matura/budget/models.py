from django.db import models
from core.models import BaseModel
from django.conf import settings

class Category(BaseModel):
    class CategoryType(models.TextChoices):
        INCOME  = 'income',  'Income'
        EXPENSE = 'expense', 'Expense'

    name          = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=CategoryType.choices)
    user          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)  # null = default/system category

    def __str__(self):
        return f"{self.name} ({self.category_type})"


class Income(BaseModel):
    class RecurrencePeriod(models.TextChoices):
        NONE       = 'none',    'None'
        WEEKLY     = 'weekly',  'Weekly'
        BIWEEKLY   = 'biweekly','Biweekly'
        MONTHLY    = 'monthly', 'Monthly'
        YEARLY     = 'yearly',  'Yearly'

    user             = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='incomes')
    category         = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    source           = models.CharField(max_length=200)
    amount           = models.DecimalField(max_digits=12, decimal_places=2)
    date             = models.DateField()
    is_recurring     = models.BooleanField(default=False)
    recurrence_period= models.CharField(max_length=10, choices=RecurrencePeriod.choices, default=RecurrencePeriod.NONE)
    notes            = models.TextField(blank=True)


class Expense(BaseModel):
    class RecurrencePeriod(models.TextChoices):
        NONE     = 'none',    'None'
        WEEKLY   = 'weekly',  'Weekly'
        BIWEEKLY = 'biweekly','Bi-Weekly'
        MONTHLY  = 'monthly', 'Monthly'
        YEARLY   = 'yearly',  'Yearly'

    user             = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expenses')
    category         = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    description      = models.CharField(max_length=200)
    amount           = models.DecimalField(max_digits=12, decimal_places=2)
    date             = models.DateField()
    is_recurring     = models.BooleanField(default=False)
    recurrence_period= models.CharField(max_length=10, choices=RecurrencePeriod.choices, default=RecurrencePeriod.NONE)
    notes            = models.TextField(blank=True)


class BudgetPeriod(BaseModel):
    """Represents one month's budget snapshot and investment suggestion."""
    user                    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budget_periods')
    month                   = models.PositiveSmallIntegerField()  # 1-12
    year                    = models.PositiveIntegerField()
    total_income            = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expenses          = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    suggested_invest_pct    = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)
    suggested_invest_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_locked               = models.BooleanField(default=False)  # lock after period ends

    class Meta:
        unique_together = ('user', 'month', 'year')

    @property
    def leftover(self):
        return self.total_income - self.total_expenses
