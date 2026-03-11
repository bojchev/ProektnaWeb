from django.db import models
from django.conf import settings
from core.models import BaseModel


class Portfolio(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='portfolio'
    )
    name = models.CharField(max_length=100, default='My Portfolio')
    cash = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username}'s Portfolio"


class Security(BaseModel):
    class AssetType(models.TextChoices):
        STOCK           = 'stock',           'Stock'
        BOND            = 'bond',            'Bond'
        INVESTMENT_FUND = 'investment_fund', 'Investment Fund'
        PENSION_FUND    = 'pension_fund',    'Pension Fund'
        CRYPTO          = 'crypto',          'Crypto'
        BANK_DEPOSIT    = 'bank_deposit',    'Bank Deposit'

    ticker     = models.CharField(max_length=30, blank=True)
    name       = models.CharField(max_length=200)
    asset_type = models.CharField(max_length=20, choices=AssetType.choices)
    exchange   = models.CharField(max_length=50, blank=True)
    requires_manual_tracking = models.BooleanField(default=False)
    interest_rate = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    maturity_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.asset_type in [self.AssetType.BANK_DEPOSIT, self.AssetType.PENSION_FUND]:
            self.requires_manual_tracking = True
        super().save(*args, **kwargs)

    def __str__(self):
        identifier = self.ticker if self.ticker else self.name
        return f"{identifier} ({self.get_asset_type_display()})"


class Holding(BaseModel):
    portfolio    = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='holdings')
    security     = models.ForeignKey(Security, on_delete=models.PROTECT, related_name='holdings')
    quantity     = models.DecimalField(max_digits=18, decimal_places=8)
    average_cost = models.DecimalField(max_digits=14, decimal_places=4)
    manual_current_price = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)

    class Meta:
        unique_together = ('portfolio', 'security')

    @property
    def total_cost_basis(self):
        if self.quantity is None or self.average_cost is None:
            return None
        return self.quantity * self.average_cost

    def __str__(self):
        return f"{self.portfolio.user.username} | {self.security.ticker or self.security.name} x{self.quantity}"


class Transaction(BaseModel):
    class TransactionType(models.TextChoices):
        BUY      = 'buy',      'Buy'
        SELL     = 'sell',     'Sell'
        DEPOSIT  = 'deposit',  'Cash Deposit'
        WITHDRAW = 'withdraw', 'Cash Withdrawal'

    portfolio        = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='transactions')
    security         = models.ForeignKey(Security, on_delete=models.PROTECT, null=True, blank=True)
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    quantity         = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    price            = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    fees             = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    date             = models.DateField()
    notes            = models.TextField(blank=True)
    from_budget      = models.BooleanField(default=False)

    @property
    def total_value(self):
        if self.quantity is None or self.price is None:
            return None
        return (self.quantity * self.price) + self.fees

    def __str__(self):
        sec = self.security.ticker if self.security else "Cash"
        return f"{self.transaction_type.upper()} | {sec} | {self.date}"
