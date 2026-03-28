
from django.db import models
from django.conf import settings
from decimal import Decimal


from core.models import BaseModel


class Goal(BaseModel):
    user          = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='goals'
    )
    name          = models.CharField(max_length=200)
    target_amount = models.DecimalField(max_digits=14, decimal_places=2)
    target_date   = models.DateField()
    is_completed  = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    @property
    def days_remaining(self):
        from django.utils import timezone
        delta = self.target_date - timezone.now().date()
        return max(delta.days, 0)

    @property
    def progress_pct(self):
        return self.progress_percentage

    @property
    def remaining(self):
        return max(self.target_amount - self.total_contributed, Decimal('0'))



    @property
    def total_contributed(self):
        return sum(c.amount for c in self.contributions.all())

    @property
    def progress_percentage(self):
        if not self.target_amount:
            return Decimal('0.00')
        pct = (self.total_contributed / self.target_amount) * 100
        return min(pct, Decimal('100.00'))

    @property
    def is_reached(self):
        if not self.target_amount:
            return False
        return self.total_contributed >= self.target_amount

    def save(self, *args, **kwargs):
        # Only check completion on existing objects, not on first creation
        if self.pk and self.is_reached:
            self.is_completed = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} | {self.name} | {self.progress_percentage:.1f}%"


class GoalContribution(BaseModel):
    goal   = models.ForeignKey(
        Goal,
        on_delete=models.CASCADE,
        related_name='contributions'

    )


    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date   = models.DateField()
    notes  = models.TextField(blank=True)

    def __str__(self):
        return f"{self.goal.name} | +{self.amount} | {self.date}"

