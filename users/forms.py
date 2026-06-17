"""
Forms for the users module.

`UserCreationForm` and `UserChangeForm` mirror Django's built-in
auth forms (so the admin keeps working out of the box) but are
adapted for the custom email-unique / UUID-pk User model.
`ProfileUpdateForm` is the form intended for end-user self-service
profile edits.
"""
from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm

from users.validators import validate_avatar_image, validate_unique_email, validate_username

User = get_user_model()


class UserCreationForm(DjangoUserCreationForm):
    """Form for creating a new user (used by the admin's 'add user' view)."""

    email = forms.EmailField(required=True)

    class Meta(DjangoUserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_username(self) -> str:
        username = self.cleaned_data["username"]
        validate_username(username)
        return username

    def clean_email(self) -> str:
        email = self.cleaned_data["email"]
        validate_unique_email(email, User)
        return email


class UserChangeForm(DjangoUserChangeForm):
    """Form for editing an existing user (used by the admin's 'change user' view)."""

    class Meta(DjangoUserChangeForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for a user updating their own profile.

    Deliberately excludes `email`, `username`, and permission fields:
    use `UserService.change_email` for email changes, which carries
    its own uniqueness validation and business rules.
    """

    class Meta:
        model = User
        fields = ("first_name", "last_name", "avatar")

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar:
            validate_avatar_image(avatar)
        return avatar
