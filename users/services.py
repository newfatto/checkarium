import secrets
from typing import Any

import requests
from django.conf import settings
from django.utils import timezone

from .models import CustomUser
import os

from users.timezone_services import get_user_local_now

from pets.models import Event, Pet
from pets.services import get_no_handling_until, get_next_repeat_datetime

from urllib.parse import urljoin

from django.conf import settings

from django.urls import reverse

from dotenv import load_dotenv



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



def get_pet_tasks_for_today(pet: Pet, user) -> list[str]:
    """Возвращает список дел на сегодня по питомцу."""
    tasks: list[str] = ["поменяй воду"]

    today = get_user_local_now(user).date()

    event_type_map = {
        Event.EventType.FEEDING: "покормить",
        Event.EventType.CLEANING: "сделать уборку",
        Event.EventType.MEASUREMENT: "измерить и взвесить",
    }

    for event_type, task_label in event_type_map.items():
        last_event = (
            pet.events.filter(
                event_type=event_type,
                repeat_after_days__isnull=False,
            )
            .order_by("-event_datetime", "-pk")
            .first()
        )

        if not last_event:
            continue

        next_dt = get_next_repeat_datetime(last_event)
        if not next_dt:
            continue

        local_next_dt = next_dt.astimezone(get_user_local_now(user).tzinfo)
        if local_next_dt.date() == today:
            tasks.append(task_label)

    custom_events = pet.events.filter(
        event_type=Event.EventType.CUSTOM,
    ).order_by("-event_datetime")

    for event in custom_events:
        next_dt = get_next_repeat_datetime(event)
        if not next_dt:
            continue

        local_next_dt = next_dt.astimezone(get_user_local_now(user).tzinfo)
        if local_next_dt.date() == today:
            event_name = event.title.strip() if event.title else "другое событие"
            tasks.append(event_name)

    return tasks


def build_daily_care_notification_text(user: CustomUser) -> str:
    """Собирает ежедневное сообщение об уходе для пользователя."""
    lines: list[str] = [f"Приветствую, {user.first_name or user.email}!", ""]

    pets = user.pets.prefetch_related("events").order_by("name")
    user_tz = get_user_local_now(user).tzinfo

    for pet in pets:
        lines.append(pet.name)

        latest_no_handling_event = (
            pet.events.filter(no_handling_days__isnull=False)
            .order_by("-event_datetime", "-pk")
            .first()
        )
        until_dt = get_no_handling_until(latest_no_handling_event) if latest_no_handling_event else None

        if until_dt and until_dt > timezone.now():
            lines.append("нельзя брать на руки")
        else:
            lines.append("можно брать на руки")

        shedding_event = (
            pet.events.filter(
                event_type=Event.EventType.SHEDDING,
                no_handling_days__isnull=False,
            )
            .order_by("-event_datetime", "-pk")
            .first()
        )

        if shedding_event:
            shedding_until = get_no_handling_until(shedding_event)
            if shedding_until and shedding_until > timezone.now():
                local_shedding_until = shedding_until.astimezone(user_tz)
                lines.append(f"линька до {local_shedding_until.strftime('%d.%m.%Y %H:%M')}")

        tasks = get_pet_tasks_for_today(pet, user)
        if tasks:
            lines.append("")
            lines.append("Важные дела на сегодня:")
            for task in tasks:
                lines.append(f"- {task}")

        lines.append("")

    lines.append("Если есть событие по уходу за питомцем, добавь его на странице:")
    lines.append(urljoin(settings.SITE_URL.rstrip("/") + "/", "pets/events/"))

    return "\n".join(lines)

def should_send_daily_notification_now(user: CustomUser) -> bool:
    """Проверяет, нужно ли отправить пользователю ежедневное уведомление сейчас."""
    if not user.care_notifications_enabled:
        return False

    if not user.telegram_id:
        return False

    local_now = get_user_local_now(user)

    # if local_now.hour != 7:
    #     return False
    #
    # if local_now.minute >= 15:
    #     return False


# Для тестирования:
    if local_now.hour != 23:
        return False

    if local_now.minute >= 59:
        return False

    if user.last_care_notification_date == local_now.date():
        return False

    # return True

# Для тестирования:
    return user.care_notifications_enabled and bool(user.telegram_id)


