import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError

UTC_OFFSET_PATTERN = re.compile(r"^UTC[+-](0\d|1[0-4]):00$")


def validate_time_zone(value: str) -> None:
    """Проверяет корректность часового пояса."""
    if UTC_OFFSET_PATTERN.fullmatch(value):
        return

    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValidationError("Укажите корректный часовой пояс.") from exc
