from django.db import models
from django.conf import settings
from core.models import BaseModel


class Account(BaseModel):
    class AccountType(models.TextChoices):
        CHECKING = 'checking', 'Checking Account'
        SAVINGS = 'savings', 'Savings Account'
        CASH = 'cash', 'Physical Cash'
        CREDIT = 'credit', 'Credit Card'
        LOAN = 'loan', 'Personal/Auto Loan'
        MORTGAGE = 'mortgage', 'Mortgage'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vault_accounts'
    )
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=AccountType.choices)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)

    # Optional fields for debts
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    credit_limit = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    @property
    def is_liability(self):
        """Returns True if this account represents debt."""
        return self.account_type in [self.AccountType.CREDIT, self.AccountType.LOAN, self.AccountType.MORTGAGE]

    def __str__(self):
        return f"{self.user.username} | {self.name} | {self.balance}"
