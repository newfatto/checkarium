from django.urls import path

from .apps import UsersConfig
from .views import (
    CustomLoginView,
    CustomLogoutView,
    ProfileDeleteView,
    ProfileDetailView,
    ProfileUpdateView,
    RegisterView,
    TelegramConnectView,
    TelegramDisableView,
    TelegramEnableView,
)

app_name = UsersConfig.name

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("profile/<int:pk>/", ProfileDetailView.as_view(), name="profile_detail"),
    path("profile/<int:pk>/update/", ProfileUpdateView.as_view(), name="profile_update"),
    path("profile/<int:pk>/delete/", ProfileDeleteView.as_view(), name="profile_delete"),
    path(
        "profile/<int:pk>/telegram/connect/",
        TelegramConnectView.as_view(),
        name="telegram_connect",
    ),
    path(
        "profile/<int:pk>/telegram/enable/",
        TelegramEnableView.as_view(),
        name="telegram_enable",
    ),
    path(
        "profile/<int:pk>/telegram/disable/",
        TelegramDisableView.as_view(),
        name="telegram_disable",
    ),
]
