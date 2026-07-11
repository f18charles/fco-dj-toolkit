from django.urls import path

from authentication.auth_methods.oauth2.views import OAuth2RedirectView, OAuth2CallbackView

app_name = "oauth2_auth"

urlpatterns = [
    path("<str:provider>/login/", OAuth2RedirectView.as_view(), name="login"),
    path("<str:provider>/callback/", OAuth2CallbackView.as_view(), name="callback"),
]
