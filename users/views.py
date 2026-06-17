"""
Views for the users module.

Kept intentionally thin: all business logic lives in `UserService`
and all read access goes through `users.selectors`. Views only
handle HTTP concerns (auth checks, form binding, redirects).
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, UpdateView

from users.exceptions import UserModuleError
from users.forms import ProfileUpdateForm
from users.permissions import can_deactivate_user
from users.services import UserService

User = get_user_model()


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """Read-only display of a user's profile."""

    model = User
    template_name = "users/profile_detail.html"
    context_object_name = "profile_user"


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Lets a logged-in user update their own first/last name and avatar."""

    model = User
    form_class = ProfileUpdateForm
    template_name = "users/profile_update.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        UserService.update_profile(user_id=self.request.user.pk, **form.cleaned_data)
        return redirect(self.success_url)


class DeactivateUserView(LoginRequiredMixin, View):
    """Deactivates a target user; all business logic lives in UserService."""

    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk)

        if not can_deactivate_user(request.user, target):
            return HttpResponseForbidden("You may not deactivate this user.")

        try:
            UserService.deactivate_user(user_id=target.pk)
        except UserModuleError as exc:
            return render(request, "users/error.html", {"message": str(exc)}, status=400)

        return redirect("users:profile")
