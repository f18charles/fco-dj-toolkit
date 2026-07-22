import pytest

pytest.importorskip("rest_framework", reason="requires djangorestframework")

from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.permissions import IsAuthenticated
from django.urls import path

from permissions.services import PermissionService, RoleService, ObjectPermissionService, ScopedPermissionService
from permissions.drf.permissions import (
    HasPermission,
    HasRole,
    HasAnyPermission,
    HasObjectPermission,
    HasScopedPermission,
)
from permissions.tests.factories import UserFactory, PermissionFactory


# Test Views for DRF Integration

class StandardPermView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "posts.edit"

    def get(self, request):
        return Response({"status": "ok"})


class StandardRoleView(APIView):
    permission_classes = [IsAuthenticated, HasRole]
    required_role = "editor"

    def get(self, request):
        return Response({"status": "ok"})


class StandardAnyPermView(APIView):
    permission_classes = [IsAuthenticated, HasAnyPermission]
    required_permissions = ["posts.edit", "posts.publish"]

    def get(self, request):
        return Response({"status": "ok"})


class ObjectPermDetailView(APIView):
    permission_classes = [IsAuthenticated, HasObjectPermission]
    required_permission = "posts.edit"

    def get(self, request, pk):
        target_user = UserFactory.build(pk=pk)
        self.check_object_permissions(request, target_user)
        return Response({"status": "ok"})


class ScopedPermView(APIView):
    permission_classes = [IsAuthenticated, HasScopedPermission]
    required_permission = "posts.edit"

    def get_permission_scope(self):
        return getattr(self, "test_scope", None)

    def get(self, request):
        return Response({"status": "ok"})


urlpatterns = [
    path("test-perm/", StandardPermView.as_view()),
    path("test-role/", StandardRoleView.as_view()),
    path("test-any-perm/", StandardAnyPermView.as_view()),
    path("test-obj-perm/<int:pk>/", ObjectPermDetailView.as_view()),
    path("test-scoped-perm/", ScopedPermView.as_view()),
]


@pytest.mark.django_db
class TestDRFIntegration:
    def setup_method(self):
        self.client = APIClient()

    def test_unauthenticated_request_returns_401_or_403(self) -> None:
        response = self.client.get("/test-perm/")
        assert response.status_code in (401, 403)

    def test_has_permission_success(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")

        self.client.force_authenticate(user=user)
        response = self.client.get("/test-perm/")
        assert response.status_code == 200
        assert response.data == {"status": "ok"}

    def test_has_permission_forbidden(self) -> None:
        user = UserFactory()
        self.client.force_authenticate(user=user)
        response = self.client.get("/test-perm/")
        assert response.status_code == 403

    def test_has_role(self) -> None:
        user = UserFactory()
        RoleService.create_role(name="editor")
        RoleService.assign_role(user=user, role_name="editor")

        self.client.force_authenticate(user=user)
        response = self.client.get("/test-role/")
        assert response.status_code == 200

        user_no_role = UserFactory()
        self.client.force_authenticate(user=user_no_role)
        response = self.client.get("/test-role/")
        assert response.status_code == 403

    def test_has_any_permission(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")

        self.client.force_authenticate(user=user)
        response = self.client.get("/test-any-perm/")
        assert response.status_code == 200

        user_no_perm = UserFactory()
        self.client.force_authenticate(user=user_no_perm)
        response = self.client.get("/test-any-perm/")
        assert response.status_code == 403

    def test_has_object_permission(self) -> None:
        user = UserFactory()
        target_obj = UserFactory()
        PermissionFactory(codename="posts.edit")
        ObjectPermissionService.grant(user=user, codename="posts.edit", obj=target_obj)

        self.client.force_authenticate(user=user)
        # Mock view instance target object for test URL dispatch
        response = self.client.get(f"/test-obj-perm/{target_obj.pk}/")
        assert response.status_code == 200

        user_without_obj_perm = UserFactory()
        self.client.force_authenticate(user=user_without_obj_perm)
        response = self.client.get(f"/test-obj-perm/{target_obj.pk}/")
        assert response.status_code == 403
