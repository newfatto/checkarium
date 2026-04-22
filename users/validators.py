import os
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError

UTC_OFFSET_PATTERN = re.compile(r"^UTC[+-](0\d|1[0-4]):00$")
PHONE_PATTERN = re.compile(r"^\+?[0-9\s\-()]{7,20}$")
NAME_PATTERN = re.compile(r"^[A-Za-zА-Яа-яЁё\s\-]+$")

MAX_IMAGE_SIZE_MB = 5
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def validate_time_zone(value: str) -> None:
    """Проверяет корректность часового пояса."""
    if UTC_OFFSET_PATTERN.fullmatch(value):
        return
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValidationError("Укажите корректный часовой пояс.") from exc


def validate_phone_number(value: str) -> None:
    """Проверяет формат телефона."""
    if not value:
        return
    if not PHONE_PATTERN.fullmatch(value.strip()):
        raise ValidationError("Введите корректный номер телефона в формате +79001234567")


def validate_person_name(value: str) -> None:
    """Проверяет имя/фамилию."""
    if not value:
        return
    if not NAME_PATTERN.fullmatch(value.strip()):
        raise ValidationError("Допустимы только буквы, пробел и дефис.")


def validate_image_file(image) -> None:
    """Проверяет расширение и размер изображения."""
    if not image:
        return

    ext = os.path.splitext(image.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError("Допустимы только изображения: jpg, jpeg, png, webp.")

    if image.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"Размер изображения не должен превышать {MAX_IMAGE_SIZE_MB} МБ.")
