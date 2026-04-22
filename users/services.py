import secrets
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.html import escape

from pets.models import Event, Pet
from pets.services import get_next_repeat_datetime, get_pet_shedding_until, pet_can_handle
from users.timezone_services import get_user_local_now

from .models import CustomUser


def generate_telegram_link_token() -> str:
    """Генерирует одноразовый токен для Telegram deep link."""
    return secrets.token_urlsafe(32)[:64]


def create_telegram_deep_link_for_user(user: CustomUser) -> str:
    """Создаёт и сохраняет одноразовый deep link для привязки Telegram к профилю пользователя."""
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
    """
    Привязывает Telegram chat_id к пользователю по одноразовому токену.
    Проверяет существование токена, его актуальность и отсутствие привязки chat_id
    к другому пользователю. После успешной привязки очищает токен и включает
    уведомления об уходе.
    """
    if not token:
        return None

    user = (
        CustomUser.objects.filter(telegram_link_token=token)
        .only("id", "telegram_id", "telegram_link_token", "telegram_link_token_created_at")
        .first()
    )

    if not user:
        raise ValidationError("Ссылка недействительна или уже использована.")

    if CustomUser.objects.filter(telegram_id=chat_id).exclude(pk=user.pk).exists():
        raise ValidationError("Этот Telegram-аккаунт уже привязан к другому профилю.")

    if user.telegram_link_token_created_at and user.telegram_link_token_created_at < timezone.now() - timedelta(
        hours=1
    ):
        raise ValidationError("Ссылка устарела. Запросите новую.")

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
    """Отправляет HTML-сообщение в Telegram и возвращает ответ Telegram Bot API."""
    response = requests.post(
        build_telegram_api_url("sendMessage"),
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def get_telegram_updates(offset: int | None = None) -> list[dict[str, Any]]:
    """Получает список обновлений из Telegram Bot API с учётом смещения offset."""
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


def get_pet_tasks_for_today(
    pet: Pet,
    user: CustomUser,
    *,
    local_now: datetime | None = None,
) -> list[str]:
    """
    Возвращает список задач на сегодня по питомцу в часовом поясе пользователя.
    В список всегда добавляется задача по смене воды. Дополнительно учитываются
    повторяющиеся события ухода и кастомные события, срок которых наступает
    в текущую локальную дату пользователя.
    """
    tasks: list[str] = ["поменяй воду"]

    if local_now is None:
        local_now = get_user_local_now(user)

    today = local_now.date()
    user_tz = local_now.tzinfo

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

        local_next_dt = next_dt.astimezone(user_tz)
        if local_next_dt.date() == today:
            tasks.append(task_label)

    custom_events = pet.events.filter(
        event_type=Event.EventType.CUSTOM,
    ).order_by("-event_datetime")

    for event in custom_events:
        next_dt = get_next_repeat_datetime(event)
        if not next_dt:
            continue

        local_next_dt = next_dt.astimezone(user_tz)
        if local_next_dt.date() == today:
            event_name = event.title.strip() if event.title else "другое событие"
            tasks.append(event_name)

    return tasks


PET_TELEGRAM_EMOJI: dict[str, str] = {
    Pet.AnimalType.SNAKE: "🐍",
    Pet.AnimalType.LIZARD: "🦎",
    Pet.AnimalType.TURTLE: "🐢",
    Pet.AnimalType.FROG: "🐸",
    Pet.AnimalType.SPIDER: "🕷️",
    Pet.AnimalType.SCORPION: "🦂",
    Pet.AnimalType.OTHER: "🐾",
}

TELEGRAM_TASK_LABELS: dict[str, str] = {
    "поменяй воду": "💧 Поменяй воду",
    "покормить": "🍽️ Покормить",
    "сделать уборку": "🧹 Сделать уборку",
    "измерить и взвесить": "📏 Измерить и взвесить",
}


def _capitalize_first(text: str) -> str:
    """Возвращает строку с заглавной первой буквой без изменения остального текста."""
    cleaned = text.strip()
    if not cleaned:
        return ""
    return cleaned[0].upper() + cleaned[1:]


def _get_pet_telegram_emoji(pet: Pet) -> str:
    """Подбирает эмодзи для питомца по его типу."""
    return PET_TELEGRAM_EMOJI.get(pet.animal_type, "🐾")


def _format_telegram_task(task: str) -> str:
    """Преобразует задачу в более читаемый формат для Telegram."""
    cleaned = task.strip()
    if not cleaned:
        return "📝 Действие"

    mapped = TELEGRAM_TASK_LABELS.get(cleaned.lower())
    if mapped:
        return mapped

    return f"📝 {_capitalize_first(cleaned)}"


def build_pet_notification_block(
    pet: Pet,
    user: CustomUser,
    *,
    local_now: datetime | None = None,
) -> str:
    """
    Собирает Telegram-блок с кратким статусом питомца и задачами на сегодня.
    """
    if local_now is None:
        local_now = get_user_local_now(user)

    user_tz = local_now.tzinfo

    lines: list[str] = [
        f"{_get_pet_telegram_emoji(pet)} <b>{escape(pet.name)}</b>",
    ]

    if pet_can_handle(pet):
        lines.append("✅ Можно брать на руки")
    else:
        lines.append("⛔ Сейчас лучше не трогать")

    shedding_until = get_pet_shedding_until(pet)
    if shedding_until:
        local_shedding_until = shedding_until.astimezone(user_tz)
        lines.append(f"🪶 Линька до: {local_shedding_until.strftime('%d.%m.%Y %H:%M')}")

    tasks = get_pet_tasks_for_today(pet, user, local_now=local_now)
    if tasks:
        lines.extend(
            [
                "",
                "📌 <b>Важные дела на сегодня:</b>",
            ]
        )
        lines.extend(f"• {escape(_format_telegram_task(task))}" for task in tasks)
    else:
        lines.extend(
            [
                "",
                "✨ На сегодня важных дел нет.",
            ]
        )

    return "\n".join(lines)


def build_daily_care_notification_text(user: CustomUser) -> str:
    """Собирает ежедневное Telegram-сообщение об уходе за питомцами пользователя."""
    local_now = get_user_local_now(user)

    user_name = escape(user.first_name or user.email)
    events_url = urljoin(settings.SITE_URL.rstrip("/") + "/", "pets/events/")

    pets = list(user.pets.prefetch_related("events").order_by("name"))

    lines: list[str] = [
        f"Доброе утро, <b>{user_name}</b>! ☀️",
        "",
        f"Сегодня {local_now.strftime('%d.%m.%Y')}. Вот напоминание по уходу за питомцами:",
        "",
    ]

    if not pets:
        lines.extend(
            [
                "У вас пока нет питомцев в системе.",
                "",
                "🔗 <b>Добавить питомца и события:</b>",
                events_url,
            ]
        )
        return "\n".join(lines)

    for index, pet in enumerate(pets):
        lines.append(build_pet_notification_block(pet, user, local_now=local_now))

        if index != len(pets) - 1:
            lines.extend(["", "──────────", ""])

    lines.extend(
        [
            "",
            "🔗 <b>Добавить событие по уходу:</b>",
            events_url,
        ]
    )

    return "\n".join(lines)


def should_send_daily_notification_now(user: CustomUser) -> bool:
    """
    Проверяет, нужно ли отправить пользователю ежедневное уведомление в текущий момент.
    Учитывает настройки уведомлений, наличие Telegram-привязки, локальное время
    пользователя и факт уже выполненной отправки за текущую дату.
    """
    if not user.care_notifications_enabled:
        return False

    if not user.telegram_id:
        return False

    local_now = get_user_local_now(user)

    target_hour = settings.CARE_NOTIFICATIONS_HOUR
    target_minute = settings.CARE_NOTIFICATIONS_MINUTE

    if local_now.hour != target_hour:
        return False

    if local_now.minute < target_minute or local_now.minute >= target_minute + 15:
        return False

    if user.last_care_notification_date == local_now.date():
        return False

    return True


def unlink_telegram_account(user: CustomUser) -> None:
    """Отвязывает Telegram от пользователя и выключает уведомления."""
    user.telegram_id = None
    user.telegram_linked_at = None
    user.telegram_link_token = None
    user.telegram_link_token_created_at = None
    user.care_notifications_enabled = False
    user.last_care_notification_date = None
    user.save(
        update_fields=[
            "telegram_id",
            "telegram_linked_at",
            "telegram_link_token",
            "telegram_link_token_created_at",
            "care_notifications_enabled",
            "last_care_notification_date",
        ]
    )


def build_telegram_welcome_text(user: CustomUser) -> str:
    """Собирает приветственное сообщение после подключения Telegram."""
    profile_url = urljoin(
        settings.SITE_URL.rstrip("/") + "/",
        user.get_absolute_url().lstrip("/"),
    )

    return (
        f"Приветствую, {user.first_name or user.email}!\n\n"
        "Теперь вы будете получать ежедневные уведомления об уходе за своими питомцами.\n\n"
        "Добавить питомцев и события вы можете в своём профиле:\n"
        f"{profile_url}"
    )
