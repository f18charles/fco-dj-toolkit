import pytest
import asyncio
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory

from permissions.decorators import (
    permission_required,
    role_required,
    any_permission_required,
    all_permissions_required,
)
from permissions.services import PermissionService, RoleService
from permissions.tests.factories import PermissionFactory
from users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestDecorators:
    def test_permission_required_allows_access(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")

        rf = RequestFactory()
        request = rf.get("/some-path/")
        request.user = user

        @permission_required("posts.edit")
        def my_view(request):
            return HttpResponse("success")

        response = my_view(request)
        assert response.content == b"success"

    def test_permission_required_denies_raises_403(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")

        rf = RequestFactory()
        request = rf.get("/some-path/")
        request.user = user

        @permission_required("posts.edit", raise_exception=True)
        def my_view(request):
            return HttpResponse("success")

        with pytest.raises(PermissionDenied):
            my_view(request)

    def test_permission_required_redirects(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")

        rf = RequestFactory()
        request = rf.get("/some-path/")
        request.user = user

        @permission_required("posts.edit", raise_exception=False)
        def my_view(request):
            return HttpResponse("success")

        response = my_view(request)
        assert response.status_code == 302
        assert "login" in response["Location"]

    def test_permission_required_async_view(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")

        rf = RequestFactory()
        request = rf.get("/some-path/")
        request.user = user

        @permission_required("posts.edit")
        async def my_async_view(request):
            return HttpResponse("success async")

        response = asyncio.run(my_async_view(request))
        assert response.content == b"success async"

    def test_role_required_allows_access(self) -> None:
        user = UserFactory()
        RoleService.create_role(name="editor")
        RoleService.assign_role(user=user, role_name="editor")

        rf = RequestFactory()
        request = rf.get("/some-path/")
        request.user = user

        @role_required("editor")
        def my_view(request):
            return HttpResponse("success role")

        response = my_view(request)
        assert response.content == b"success role"

    def test_role_required_denies_raises_403(self) -> None:
        user = UserFactory()
        RoleService.create_role(name="editor")

        rf = RequestFactory()
        request = rf.get("/some-path/")
        request.user = user

        @role_required("editor", raise_exception=True)
        def my_view(request):
            return HttpResponse("success")

        with pytest.raises(PermissionDenied):
            my_view(request)

    def test_any_permission_required(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        PermissionFactory(codename="posts.delete")
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")

        rf = RequestFactory()
        request = rf.get("/some-path/")
        request.user = user

        @any_permission_required(["posts.edit", "posts.delete"])
        def my_view(request):
            return HttpResponse("success any")

        response = my_view(request)
        assert response.content == b"success any"

    def test_all_permissions_required(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        PermissionFactory(codename="posts.delete")
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")

        rf = RequestFactory()
        request = rf.get("/some-path/")
        request.user = user

        @all_permissions_required(["posts.edit", "posts.delete"])
        def my_view(request):
            return HttpResponse("success")

        with pytest.raises(PermissionDenied):
            my_view(request)
