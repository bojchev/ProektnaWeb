from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from decimal import Decimal
from core.models import BaseModel


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


class UserProfile(BaseModel):
    class RiskTolerance(models.TextChoices):
        CONSERVATIVE = 'conservative', 'Conservative'
        MODERATE     = 'moderate',     'Moderate'
        AGGRESSIVE   = 'aggressive',   'Aggressive'

    RISK_DEFAULTS = {
        'conservative': Decimal('10.00'),
        'moderate':     Decimal('20.00'),
        'aggressive':   Decimal('30.00'),
    }

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    risk_tolerance = models.CharField(
        max_length=20,
        choices=RiskTolerance.choices,
        default=RiskTolerance.MODERATE
    )
    custom_invest_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Overrides risk tolerance suggestion. Leave blank to use default."
    )

    @property
    def suggested_invest_percentage(self):
        if self.custom_invest_percentage is not None:
            return self.custom_invest_percentage
        return self.RISK_DEFAULTS.get(self.risk_tolerance, Decimal('20.00'))

    @property
    def invest_percentage(self):
        return self.suggested_invest_percentage

    def __str__(self):
        return f"{self.user.username} - {self.risk_tolerance}"
