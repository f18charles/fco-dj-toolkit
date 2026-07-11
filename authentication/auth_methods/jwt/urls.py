from django.urls import path

from authentication.auth_methods.jwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)

app_name = "jwt_auth"

urlpatterns = [
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("revoke/", TokenBlacklistView.as_view(), name="revoke"),
]
