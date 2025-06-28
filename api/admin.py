from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.action(description="Make selected users Clients")
def make_client(modeladmin, request, queryset):
    queryset.update(role='client')

@admin.action(description="Make selected users Managers")
def make_manager(modeladmin, request, queryset):
    queryset.update(role='manager')

@admin.action(description="Make selected users Admins")
def make_admin(modeladmin, request, queryset):
    queryset.update(role='admin')

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['email', 'role', 'is_staff']
    ordering = ['email']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )
    actions = [make_client, make_manager, make_admin]  # ✅ Add actions here

admin.site.register(User, CustomUserAdmin)
