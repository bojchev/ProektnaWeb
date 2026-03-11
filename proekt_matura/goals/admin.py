from django.contrib import admin
from .models import Goal, GoalContribution


class GoalContributionInline(admin.TabularInline):
    model = GoalContribution
    extra = 0
    fields = ('amount', 'date', 'notes')



@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'target_amount', 'total_contributed', 'progress_percentage', 'target_date', 'is_completed')
    list_filter = ('is_completed',)
    search_fields = ('name', 'user__username')
    readonly_fields = ('total_contributed', 'progress_percentage', 'is_completed')
    inlines = (GoalContributionInline,)


@admin.register(GoalContribution)
class GoalContributionAdmin(admin.ModelAdmin):
    list_display = ('goal', 'amount', 'date')
    search_fields = ('goal__name', 'goal__user__username')
    date_hierarchy = 'date'
    ordering = ('-date',)
