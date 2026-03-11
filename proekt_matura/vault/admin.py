from django.contrib import admin
from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'account_type', 'balance', 'is_liability', 'interest_rate', 'credit_limit')
    list_filter = ('account_type',)
    search_fields = ('name', 'user__username')
    readonly_fields = ('is_liability', 'created_at', 'updated_at')

    fieldsets = (
        ('General', {
            'fields': ('user', 'name', 'account_type', 'balance')
        }),
        ('Debt Details (Credit/Loan/Mortgage only)', {
            'fields': ('interest_rate', 'credit_limit'),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('is_liability', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
