from django.contrib import admin
from authentication.core.models import LoginAttempt

# Register LoginAttempt as a read-only admin tool
@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ("identifier", "was_successful", "ip_address", "created_at")
    list_filter = ("was_successful", "created_at")
    search_fields = ("identifier", "ip_address", "failure_reason")
    
    # Restrict modifications
    readonly_fields = (
        "id",
        "user",
        "identifier",
        "ip_address",
        "user_agent",
        "was_successful",
        "failure_reason",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False


# Guarded session admin registration to support modular, opt-in configurations
try:
    from authentication.auth_methods.session.models import UserSession

    @admin.register(UserSession)
    class UserSessionAdmin(admin.ModelAdmin):
        list_display = ("user", "session_key", "is_active", "ip_address", "last_activity")
        list_filter = ("is_active", "last_activity")
        search_fields = ("user__email", "user__username", "session_key", "ip_address")
        
        readonly_fields = (
            "id",
            "user",
            "session_key",
            "ip_address",
            "user_agent",
            "is_active",
            "last_activity",
            "created_at",
            "updated_at",
        )

        def has_add_permission(self, request) -> bool:
            return False

        def has_delete_permission(self, request, obj=None) -> bool:
            return False

        def has_change_permission(self, request, obj=None) -> bool:
            return False

except ImportError:
    # If session module is excluded or unavailable, skip registering UserSession admin
    pass


# Guarded social account admin registration
try:
    from authentication.auth_methods.oauth2.models import SocialAccount

    @admin.register(SocialAccount)
    class SocialAccountAdmin(admin.ModelAdmin):
        list_display = ("user", "provider", "provider_user_id", "created_at")
        list_filter = ("provider", "created_at")
        search_fields = ("user__email", "user__username", "provider_user_id")

        readonly_fields = (
            "id",
            "user",
            "provider",
            "provider_user_id",
            "created_at",
            "updated_at",
        )

        def has_add_permission(self, request) -> bool:
            return False

        def has_delete_permission(self, request, obj=None) -> bool:
            return False

        def has_change_permission(self, request, obj=None) -> bool:
            return False

except ImportError:
    # If oauth2 module is excluded or unavailable, skip registering SocialAccount admin
    pass

