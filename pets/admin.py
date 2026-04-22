from django.contrib import admin

from .models import Event, Pet


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    """Настройки отображения модели питомца в админке."""

    list_display = (
        "id",
        "name",
        "species_name",
        "animal_type",
        "owner",
        "sex",
        "status",
        "is_public",
        "created_at",
    )
    list_filter = (
        "animal_type",
        "sex",
        "status",
        "is_public",
        "created_at",
    )
    search_fields = (
        "name",
        "species_name",
        "morph",
        "owner__email",
        "owner__first_name",
        "owner__last_name",
    )
    autocomplete_fields = ("owner",)
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("owner",)
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "owner",
                    "name",
                    "animal_type",
                    "species_name",
                    "morph",
                    "sex",
                    "status",
                    "is_public",
                )
            },
        ),
        (
            "Даты и размеры",
            {
                "fields": (
                    "birth_date",
                    "acquired_date",
                    "weight_grams",
                    "length_cm",
                )
            },
        ),
        (
            "Дополнительно",
            {
                "fields": (
                    "photo",
                    "feeding_notes",
                    "notes",
                )
            },
        ),
        (
            "Служебные поля",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Настройки отображения модели события в админке."""

    list_display = (
        "id",
        "pet",
        "event_type",
        "event_datetime",
        "owner",
        "repeat_after_days",
        "no_handling_days",
        "created_at",
    )
    list_filter = (
        "event_type",
        "event_datetime",
        "created_at",
    )
    search_fields = (
        "pet__name",
        "pet__species_name",
        "owner__email",
        "title",
        "comment",
    )
    autocomplete_fields = ("owner", "pet")
    readonly_fields = ("created_at",)
    list_select_related = ("owner", "pet")
    ordering = ("-event_datetime",)

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "owner",
                    "pet",
                    "event_type",
                    "title",
                    "event_datetime",
                    "comment",
                )
            },
        ),
        (
            "Параметры события",
            {
                "fields": (
                    "repeat_after_days",
                    "no_handling_days",
                    "weight_grams",
                    "length_cm",
                )
            },
        ),
        (
            "Служебные поля",
            {"fields": ("created_at",)},
        ),
    )
