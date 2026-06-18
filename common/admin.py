from django.contrib import admin


class BaseAdmin(admin.ModelAdmin):
    """
    Base Admin class providing common configuration, layout defaults, or extensions
    for the admin panel across modules.
    """
    pass
