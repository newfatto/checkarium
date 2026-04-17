from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Админка для кастомной модели пользователя."""

    model = CustomUser

    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "city",
        "phone_number",
        "telegram_id",
        "is_staff",
        "is_active",
        "time_zone",
    )
    list_filter = (
        "is_staff",
        "is_active",
        "is_superuser",
        "city",
    )
    search_fields = (
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "city",
    )
    ordering = ("id",)

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "email",
                    "password",
                    "first_name",
                    "last_name",
                    "city",
                    "phone_number",
                    "avatar",
                    "bio",
                    "telegram_id",
                    "time_zone",
                )
            },
        ),
        (
            "Права доступа",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Даты",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            "Создание пользователя",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )