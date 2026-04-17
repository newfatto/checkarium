from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError


def validate_time_zone(value: str) -> None:
    """Проверяет, что строка является корректным IANA-часовым поясом."""
    if not value:
        raise ValidationError("Укажите часовой пояс.")

    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValidationError("Укажите корректный часовой пояс, например Europe/Moscow.") from exc