from django.urls import path

from authentication.auth_methods.token.views import ObtainTokenView, RevokeTokenView

app_name = "token_auth"

urlpatterns = [
    path("login/", ObtainTokenView.as_view(), name="login"),
    path("revoke/", RevokeTokenView.as_view(), name="revoke"),
]
