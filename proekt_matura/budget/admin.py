from django.contrib import admin
from .models import Category, Income, Expense


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'is_preset', 'user')
    list_filter = ('category_type', 'is_preset')
    search_fields = ('name', 'user__username')


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('user', 'description', 'amount', 'category', 'date')
    list_filter = ('category', 'date')
    search_fields = ('user__username', 'description')
    date_hierarchy = 'date'
    ordering = ('-date',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'description', 'amount', 'category', 'date')
    list_filter = ('category', 'date')
    search_fields = ('user__username', 'description')
    date_hierarchy = 'date'
    ordering = ('-date',)
