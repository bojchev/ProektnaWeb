from django.contrib.auth.models import AbstractUser
from django.db import models
from core.models import BaseModel

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

class UserProfile(BaseModel):
    class RiskTolerance(models.TextChoices):
        CONSERVATIVE = 'conservative', 'Conservative'
        MODERATE     = 'moderate',     'Moderate'
        AGGRESSIVE   = 'aggressive',   'Aggressive'

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    risk_tolerance = models.CharField(max_length=20, choices=RiskTolerance.choices, default=RiskTolerance.MODERATE)
    default_invest_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)  # e.g. 20%
