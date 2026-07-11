from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.core.exceptions import AuthenticationModuleError
from authentication.core.services import AuthService
from authentication.auth_methods.token import services as token_services


class ObtainTokenView(APIView):
    """
    API view to authenticate credentials and issue a standard DRF auth token.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs) -> Response:
        identifier = request.data.get("identifier")
        password = request.data.get("password")

        if not identifier or not password:
            return Response(
                {"error": "Both identifier and password are required.", "code": "missing_fields"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = AuthService.verify_credentials(
                identifier=identifier,
                password=password,
                request=request,
            )
            token = token_services.issue(user)
            return Response({"token": token.key, "user_id": str(user.pk)})
        except AuthenticationModuleError as e:
            return Response(
                {"error": e.message, "code": e.code},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RevokeTokenView(APIView):
    """
    API view to revoke (delete) the authenticated user's DRF auth token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs) -> Response:
        token_services.revoke(request.user)
        return Response({"message": "Token revoked successfully."}, status=status.HTTP_200_OK)
