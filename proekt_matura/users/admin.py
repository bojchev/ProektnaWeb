from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('risk_tolerance', 'custom_invest_percentage')


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'risk_tolerance', 'get_custom_invest_pct', 'get_suggested_invest_pct')
    list_filter = ('risk_tolerance',)
    search_fields = ('user__username',)
    readonly_fields = ('get_suggested_invest_pct',)


    @admin.display(description='Custom Invest %')
    def get_custom_invest_pct(self, obj):
        return obj.custom_invest_percentage if obj.custom_invest_percentage is not None else '—'

    @admin.display(description='Effective Invest %')
    def get_suggested_invest_pct(self, obj):
        return f"{obj.suggested_invest_percentage}%"
