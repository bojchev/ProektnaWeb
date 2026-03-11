from django.contrib import admin
from .models import Portfolio, Security, Holding, Transaction


class HoldingInline(admin.TabularInline):
    model = Holding
    extra = 0
    readonly_fields = ('total_cost_basis',)
    fields = ('security', 'quantity', 'average_cost', 'manual_current_price', 'total_cost_basis')


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    fields = ('transaction_type', 'security', 'quantity', 'price', 'fees', 'date', 'from_budget')
    readonly_fields = ('total_value',)


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'cash')
    search_fields = ('user__username', 'name')
    inlines = (HoldingInline, TransactionInline)


@admin.register(Security)
class SecurityAdmin(admin.ModelAdmin):
    list_display = ('name', 'ticker', 'asset_type', 'exchange', 'requires_manual_tracking', 'interest_rate', 'maturity_date')
    list_filter = ('asset_type', 'requires_manual_tracking')
    search_fields = ('name', 'ticker')

    fieldsets = (
        ('General', {
            'fields': ('name', 'ticker', 'asset_type', 'exchange', 'requires_manual_tracking')
        }),
        ('Yield / Deposit Details (optional)', {
            'fields': ('interest_rate', 'maturity_date'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ('portfolio', 'security', 'quantity', 'average_cost', 'total_cost_basis', 'manual_current_price')
    search_fields = ('portfolio__user__username', 'security__ticker', 'security__name')
    readonly_fields = ('total_cost_basis',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('portfolio', 'transaction_type', 'security', 'quantity', 'price', 'fees', 'date', 'from_budget', 'total_value')
    list_filter = ('transaction_type', 'from_budget', 'date')
    search_fields = ('portfolio__user__username', 'security__ticker')
    date_hierarchy = 'date'
    ordering = ('-date',)
    readonly_fields = ('total_value',)
