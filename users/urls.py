"""
URL routes for the users module.

Include in a project's root URLconf with:

    path("users/", include("users.urls")),
"""
from django.urls import path

from users import views

app_name = "users"

urlpatterns = [
    path("profile/", views.ProfileDetailView.as_view(), name="profile"),
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile-edit"),
    path("<uuid:pk>/deactivate/", views.DeactivateUserView.as_view(), name="deactivate"),
]
