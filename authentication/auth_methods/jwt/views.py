from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView as SimpleJWTTokenRefreshView

from authentication.core.exceptions import AuthenticationModuleError
from authentication.core.services import AuthService
from authentication.auth_methods.jwt.services import issue_pair, revoke_refresh_token


class TokenObtainPairView(APIView):
    """
    Obtains access + refresh token pair by routing credentials verification
    through core AuthService to apply locks, throttle, and audit logging.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs) -> Response:
        identifier = request.data.get("identifier") or request.data.get("username")
        password = request.data.get("password")

        if not identifier or not password:
            return Response(
                {"error": "Both identifier and password are required.", "code": "missing_fields"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # 1. Route credential verification through the core AuthService
            user = AuthService.verify_credentials(
                identifier=identifier,
                password=password,
                request=request,
            )
            # 2. Issue the JWT pair on successful verification
            tokens = issue_pair(user)
            return Response(
                {
                    "refresh": tokens["refresh"],
                    "access": tokens["access"],
                    "user_id": str(user.pk),
                },
                status=status.HTTP_200_OK,
            )
        except AuthenticationModuleError as e:
            return Response(
                {"error": e.message, "code": e.code},
                status=status.HTTP_400_BAD_REQUEST,
            )


class TokenRefreshView(SimpleJWTTokenRefreshView):
    """
    Wraps standard simplejwt refresh endpoint.
    """
    pass


class TokenBlacklistView(APIView):
    """
    Blacklists a refresh token to revoke access.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs) -> Response:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required.", "code": "missing_refresh_token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            revoke_refresh_token(refresh_token)
            return Response({"message": "Token blacklisted successfully."}, status=status.HTTP_200_OK)
        except NotImplementedError as e:
            return Response(
                {"error": str(e), "code": "not_implemented"},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        except Exception:
            return Response(
                {"error": "Invalid token or already blacklisted.", "code": "invalid_token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
