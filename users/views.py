from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

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