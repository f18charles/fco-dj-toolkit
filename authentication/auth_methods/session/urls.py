from django.urls import path

from authentication.auth_methods.session.views import (
    LoginView,
    LogoutView,
    SessionListView,
    SessionRevokeView,
)

app_name = "session_auth"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("sessions/", SessionListView.as_view(), name="session_list"),
    path("sessions/<str:session_id>/revoke/", SessionRevokeView.as_view(), name="session_revoke"),
]
