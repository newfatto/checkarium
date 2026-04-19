from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from .services import (
    create_telegram_deep_link_for_user,
    disable_care_notifications,
    enable_care_notifications,
)

from pets.services import build_pet_card_context, build_event_row_context
from .forms import (
    CustomAuthenticationForm,
    CustomUserCreationForm,
    CustomUserUpdateForm,
)
from .models import CustomUser


class OnlyOwnerMixin(UserPassesTestMixin):
    """Миксин, разрешающий доступ только владельцу профиля."""

    def test_func(self) -> bool:
        """
        Проверить, что пользователь работает со своим профилем.

        :return: True, если пользователь владелец объекта.
        """
        return self.request.user == self.get_object()


class RegisterView(CreateView):
    """Представление для регистрации пользователя."""

    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")


class CustomLoginView(LoginView):
    """Представление для авторизации пользователя."""

    form_class = CustomAuthenticationForm
    template_name = "users/login.html"
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        """
        Вернуть URL для перенаправления после успешного входа.

        :return: URL профиля текущего пользователя.
        """
        return reverse_lazy("users:profile_detail", kwargs={"pk": self.request.user.pk})


class CustomLogoutView(LogoutView):
    """Представление для выхода пользователя из системы."""

    next_page = reverse_lazy("home")


class ProfileDetailView(LoginRequiredMixin, OnlyOwnerMixin, DetailView):
    """Представление для просмотра профиля пользователя."""

    model = CustomUser
    template_name = "users/profile.html"
    context_object_name = "profile_user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.get_object()

        latest_pets = (
            profile_user.pets.select_related("owner")
            .prefetch_related("events")
            .order_by("-created_at")[:6]
        )
        latest_events = (
            profile_user.events.select_related("pet", "owner")
            .order_by("-event_datetime")[:10]
        )

        context["profile_pet_cards"] = [
            build_pet_card_context(pet, self.request.user)
            for pet in latest_pets
        ]
        context["profile_event_rows"] = [
            build_event_row_context(event)
            for event in latest_events
        ]
        return context


class ProfileUpdateView(LoginRequiredMixin, OnlyOwnerMixin, UpdateView):
    """Представление для редактирования профиля пользователя."""

    model = CustomUser
    form_class = CustomUserUpdateForm
    template_name = "users/profile_form.html"
    context_object_name = "profile_user"

    def get_success_url(self) -> str:
        """
        Вернуть URL после успешного обновления профиля.

        :return: URL страницы профиля.
        """
        return reverse_lazy("users:profile_detail", kwargs={"pk": self.object.pk})


class ProfileDeleteView(LoginRequiredMixin, OnlyOwnerMixin, DeleteView):
    """Представление для удаления профиля пользователя."""

    model = CustomUser
    template_name = "users/profile_confirm_delete.html"
    success_url = reverse_lazy("home")
    context_object_name = "profile_user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.get_object()

        latest_pets = profile_user.pets.select_related("owner").prefetch_related("events").all()[:6]
        latest_events = profile_user.events.select_related("pet", "owner").all()[:10]

        context["profile_pet_cards"] = [
            build_pet_card_context(pet, self.request.user)
            for pet in latest_pets
        ]
        context["profile_event_rows"] = [
            build_event_row_context(event)
            for event in latest_events
        ]
        return context


class TelegramConnectView(LoginRequiredMixin, View):
    """Создаёт deep link для привязки Telegram и перенаправляет пользователя в бота."""

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        user = get_object_or_404(CustomUser, pk=pk)

        if request.user != user:
            raise PermissionDenied

        if user.telegram_id:
            enable_care_notifications(user)
            messages.success(request, "Уведомления об уходе включены.")
            return redirect("users:profile_detail", pk=user.pk)

        deep_link = create_telegram_deep_link_for_user(user)
        return redirect(deep_link)


class TelegramDisableView(LoginRequiredMixin, View):
    """Выключает уведомления об уходе."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        user = get_object_or_404(CustomUser, pk=pk)

        if request.user != user:
            raise PermissionDenied

        disable_care_notifications(user)
        messages.success(request, "Уведомления об уходе выключены.")
        return redirect("users:profile_detail", pk=user.pk)


class TelegramEnableView(LoginRequiredMixin, View):
    """Включает уведомления об уходе для уже привязанного Telegram."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        user = get_object_or_404(CustomUser, pk=pk)

        if request.user != user:
            raise PermissionDenied

        if not user.telegram_id:
            messages.error(request, "Сначала подключите Telegram через бота.")
            return redirect("users:profile_detail", pk=user.pk)

        enable_care_notifications(user)
        messages.success(request, "Уведомления об уходе включены.")
        return redirect("users:profile_detail", pk=user.pk)