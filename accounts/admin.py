from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Role, UserSession, LoginAttempt


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'description')}),
        ('Status', {'fields': ('is_active',)}),
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username', 'email', 'get_full_name', 'role', 'nim', 'nidn',
        'is_verified', 'is_active', 'last_activity', 'date_joined'
    ]
    list_filter = [
        'role', 'is_verified', 'is_active', 'is_staff', 'is_superuser',
        'faculty', 'study_program', 'enrollment_year', 'theme_preference',
        'email_notifications', 'date_joined'
    ]
    search_fields = [
        'username', 'email', 'nim', 'nidn', 'nip',
        'first_name', 'last_name', 'phone', 'bio'
    ]
    list_editable = ['role', 'is_verified']
    list_per_page = 25
    date_hierarchy = 'date_joined'

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name', 'last_name', 'email', 'phone', 'bio', 'avatar'
            )
        }),
        (_('Role & Identity'), {
            'fields': (
                'role', 'nim', 'nidn', 'nip',
                'faculty', 'study_program', 'enrollment_year'
            )
        }),
        (_('Verification & Status'), {
            'fields': (
                'is_verified', 'email_verified_at', 'is_active',
                'theme_preference', 'email_notifications'
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_staff', 'is_superuser', 'groups', 'user_permissions'
            ),
            'classes': ('collapse',),
        }),
        (_('Important dates'), {
            'fields': (
                'last_login', 'last_activity', 'date_joined', 'created_at',
                'updated_at'
            )
        }),
    )
    readonly_fields = [
        'last_login', 'date_joined', 'created_at', 'updated_at',
        'last_activity'
    ]
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2', 'role',
                'nim', 'nidn', 'nip', 'first_name', 'last_name'
            ),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'faculty', 'study_program'
        )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'is_active', 'last_activity', 'created_at']
    list_filter = ['is_active', 'last_activity']
    search_fields = ['user__username', 'user__email', 'ip_address', 'session_key']
    list_editable = ['is_active']
    date_hierarchy = 'last_activity'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['username', 'ip_address', 'was_successful', 'attempted_at']
    list_filter = ['was_successful', 'attempted_at']
    search_fields = ['username', 'ip_address', 'user_agent']
    date_hierarchy = 'attempted_at'
    readonly_fields = ['username', 'ip_address', 'user_agent', 'was_successful', 'attempted_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return False
        return super().has_change_permission(request, obj)
