import secrets
from typing import Any

import requests
from django.conf import settings
from django.utils import timezone

from .models import CustomUser


def generate_telegram_link_token() -> str:
    """Генерирует одноразовый токен для Telegram deep link."""
    return secrets.token_urlsafe(32)[:64]


def create_telegram_deep_link_for_user(user: CustomUser) -> str:
    """Создаёт deep link для привязки Telegram к профилю пользователя."""
    token = generate_telegram_link_token()

    user.telegram_link_token = token
    user.telegram_link_token_created_at = timezone.now()
    user.save(update_fields=["telegram_link_token", "telegram_link_token_created_at"])

    return f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={token}"


def enable_care_notifications(user: CustomUser) -> None:
    """Включает уведомления об уходе."""
    user.care_notifications_enabled = True
    user.save(update_fields=["care_notifications_enabled"])


def disable_care_notifications(user: CustomUser) -> None:
    """Выключает уведомления об уходе."""
    user.care_notifications_enabled = False
    user.save(update_fields=["care_notifications_enabled"])


def link_telegram_account_by_token(token: str, chat_id: int) -> CustomUser | None:
    """Привязывает Telegram chat_id к пользователю по одноразовому токену."""
    if not token:
        return None

    user = (
        CustomUser.objects.filter(telegram_link_token=token)
        .only("id", "telegram_id", "telegram_link_token")
        .first()
    )
    if not user:
        return None

    user.telegram_id = chat_id
    user.telegram_linked_at = timezone.now()
    user.telegram_link_token = None
    user.telegram_link_token_created_at = None
    user.care_notifications_enabled = True
    user.save(
        update_fields=[
            "telegram_id",
            "telegram_linked_at",
            "telegram_link_token",
            "telegram_link_token_created_at",
            "care_notifications_enabled",
        ]
    )
    return user


def build_telegram_api_url(method: str) -> str:
    """Возвращает URL метода Telegram Bot API."""
    return f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"


def send_telegram_message(chat_id: int, text: str) -> dict[str, Any]:
    """Отправляет текстовое сообщение в Telegram."""
    response = requests.post(
        build_telegram_api_url("sendMessage"),
        json={
            "chat_id": chat_id,
            "text": text,
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def get_telegram_updates(offset: int | None = None) -> list[dict[str, Any]]:
    """Получает обновления от Telegram Bot API."""
    payload: dict[str, Any] = {
        "timeout": 30,
    }
    if offset is not None:
        payload["offset"] = offset

    response = requests.get(
        build_telegram_api_url("getUpdates"),
        params=payload,
        timeout=40,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("result", [])