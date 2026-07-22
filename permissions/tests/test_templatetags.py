import pytest
from django.template import Context, Template
from django.contrib.auth.models import AnonymousUser
from permissions.services import PermissionService, RoleService, ObjectPermissionService
from permissions.tests.factories import UserFactory, PermissionFactory, RoleFactory


@pytest.mark.django_db
class TestPermissionTemplateTags:
    def test_has_permission_tag_true(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")

        template = Template(
            "{% load permissions_tags %}"
            "{% has_permission user 'posts.edit' as can_edit %}"
            "{{ can_edit }}"
        )
        rendered = template.render(Context({"user": user}))
        assert rendered.strip() == "True"

    def test_has_permission_tag_false(self) -> None:
        user = UserFactory()
        template = Template(
            "{% load permissions_tags %}"
            "{% has_permission user 'posts.edit' as can_edit %}"
            "{{ can_edit }}"
        )
        rendered = template.render(Context({"user": user}))
        assert rendered.strip() == "False"

    def test_has_role_tag(self) -> None:
        user = UserFactory()
        RoleService.create_role(name="editor")
        RoleService.assign_role(user=user, role_name="editor")

        template = Template(
            "{% load permissions_tags %}"
            "{% has_role user 'editor' as is_editor %}"
            "{% has_role user 'admin' as is_admin %}"
            "{{ is_editor }},{{ is_admin }}"
        )
        rendered = template.render(Context({"user": user}))
        assert rendered.strip() == "True,False"

    def test_has_object_permission_tag(self) -> None:
        user = UserFactory()
        target = UserFactory()
        PermissionFactory(codename="posts.edit")
        ObjectPermissionService.grant(user=user, codename="posts.edit", obj=target)

        template = Template(
            "{% load permissions_tags %}"
            "{% has_object_permission user 'posts.edit' target as can_edit %}"
            "{{ can_edit }}"
        )
        rendered = template.render(Context({"user": user, "target": target}))
        assert rendered.strip() == "True"

    def test_has_any_permission_tag(self) -> None:
        user = UserFactory()
        PermissionFactory(codename="posts.edit")
        PermissionFactory(codename="posts.publish")
        PermissionService.grant_permission_to_user(user=user, codename="posts.edit")

        template = Template(
            "{% load permissions_tags %}"
            "{% has_any_permission user 'posts.edit,posts.publish' as can_do %}"
            "{{ can_do }}"
        )
        rendered = template.render(Context({"user": user}))
        assert rendered.strip() == "True"

    def test_anonymous_user_fails_silently(self) -> None:
        anon = AnonymousUser()
        template = Template(
            "{% load permissions_tags %}"
            "{% has_permission user 'posts.edit' as p1 %}"
            "{% has_role user 'editor' as p2 %}"
            "{% has_any_permission user 'posts.edit' as p3 %}"
            "{{ p1 }},{{ p2 }},{{ p3 }}"
        )
        rendered = template.render(Context({"user": anon}))
        assert rendered.strip() == "False,False,False"
