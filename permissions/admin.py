from django.contrib import admin

from permissions.models import Permission, Role, RolePermission, UserRole, UserPermission


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("codename", "name", "module", "created_at")
    list_filter = ("module",)
    search_fields = ("codename", "name")
    ordering = ("module", "codename")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_system_role", "created_at")
    list_filter = ("is_system_role",)
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ("role", "permission", "granted_by", "created_at")
    search_fields = ("role__name", "permission__codename")
    readonly_fields = ("created_at",)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "granted_by", "expires_at", "created_at")
    list_filter = ("role",)
    search_fields = ("user__email", "user__username", "role__name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ("user", "permission", "granted_by", "expires_at", "created_at")
    search_fields = ("user__email", "permission__codename")
    readonly_fields = ("created_at", "updated_at")
