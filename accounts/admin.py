from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import UserProfile

CustomUser = get_user_model()


class CustomUserAdmin(UserAdmin):
    """Custom admin configuration for the CustomUser model."""
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile model."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile użytkowników'
    fk_name = 'user'


class CustomUserWithProfileAdmin(CustomUserAdmin):
    """Custom user admin that includes profile fields."""
    inlines = (UserProfileInline,)
    list_display = ('email', 'first_name', 'last_name', 'get_role', 'is_staff', 'is_active')
    
    def get_role(self, obj):
        return obj.profile.get_role_display()
    get_role.short_description = 'Rola'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


# Only unregister if it's already registered
if admin.site.is_registered(CustomUser):
    admin.site.unregister(CustomUser)

# Register our custom admin
admin.site.register(CustomUser, CustomUserWithProfileAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for the UserProfile model."""
    list_display = ('user', 'role', 'phone_number', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'role')
        }),
        (_('Contact Information'), {
            'fields': ('phone_number', 'address')
        }),
        (_('Personal Information'), {
            'fields': ('date_of_birth', 'profile_picture')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
