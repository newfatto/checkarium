from datetime import timedelta, timezone as dt_timezone
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone

from datetime import datetime
from django.utils import timezone


UTC_OFFSET_PATTERN = re.compile(r"^UTC(?P<sign>[+-])(?P<hours>\d{2}):(?P<minutes>\d{2})$")


def get_user_tzinfo(time_zone_value: str):
    """Возвращает tzinfo пользователя по строке часового пояса."""
    match = UTC_OFFSET_PATTERN.fullmatch(time_zone_value)
    if match:
        sign = 1 if match.group("sign") == "+" else -1
        hours = int(match.group("hours"))
        minutes = int(match.group("minutes"))
        offset = timedelta(hours=hours, minutes=minutes) * sign
        return dt_timezone(offset)

    try:
        return ZoneInfo(time_zone_value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Некорректный часовой пояс: {time_zone_value}") from exc


def activate_user_timezone(user) -> None:
    """Активирует часовой пояс пользователя для текущего запроса."""
    if user and user.is_authenticated and getattr(user, "time_zone", None):
        timezone.activate(get_user_tzinfo(user.time_zone))
    else:
        timezone.deactivate()

def get_user_local_now(user) -> datetime:
    """Возвращает текущее локальное время пользователя."""
    return timezone.now().astimezone(get_user_tzinfo(user.time_zone))