import pytest
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory
from django.views.generic import View

from permissions.mixins import PermissionRequiredMixin, RoleRequiredMixin
from permissions.services import PermissionService, RoleService
from permissions.tests.factories import PermissionFactory
from users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class MyPermissionView(PermissionRequiredMixin, View):
    required_permission = "posts.edit"
    raise_exception = True

    def get(self, request, *args, **kwargs):
        return HttpResponse("success perm view")


class MyRoleView(RoleRequiredMixin, View):
    required_role = "editor"
    raise_exception = True

    def get(self, request, *args, **kwargs):
        return HttpResponse("success role view")


class TestMixins:
    def test_permission_required_mixin_allows_access(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")

        rf = RequestFactory()
        request = rf.get("/")
        request.user = user

        view = MyPermissionView.as_view()
        response = view(request)
        assert response.content == b"success perm view"

    def test_permission_required_mixin_denies_raises_403(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")

        rf = RequestFactory()
        request = rf.get("/")
        request.user = user

        view = MyPermissionView.as_view()
        with pytest.raises(PermissionDenied):
            view(request)

    def test_role_required_mixin_allows_access(self) -> None:
        user = UserFactory()
        RoleService.create_role(name="editor")
        RoleService.assign_role(user=user, role_name="editor")

        rf = RequestFactory()
        request = rf.get("/")
        request.user = user

        view = MyRoleView.as_view()
        response = view(request)
        assert response.content == b"success role view"

    def test_role_required_mixin_denies_raises_403(self) -> None:
        user = UserFactory()
        RoleService.create_role(name="editor")

        rf = RequestFactory()
        request = rf.get("/")
        request.user = user

        view = MyRoleView.as_view()
        with pytest.raises(PermissionDenied):
            view(request)
