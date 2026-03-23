
# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'full_name', 'account_type', 'created_at']
    list_filter = ['account_type', 'is_active']
    search_fields = ['email', 'full_name']
    ordering = ['-created_at']
    fieldsets = UserAdmin.fieldsets + (
        ('Dalia Fields', {'fields': ('full_name', 'account_type', 'is_onboarded')}),
    )