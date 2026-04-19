from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Iterable

from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from .models import Event, Pet


def get_pet_age_display(birth_date: date | None) -> str:
    """Возвращает возраст питомца в удобном формате."""
    if not birth_date:
        return ""

    today = timezone.localdate()
    if birth_date > today:
        return ""

    total_days = (today - birth_date).days
    if total_days < 31:
        return f"{total_days} дн."

    years = today.year - birth_date.year
    months = today.month - birth_date.month
    days = today.day - birth_date.day

    if days < 0:
        months -= 1

        if today.month == 1:
            prev_month = 12
            prev_year = today.year - 1
        else:
            prev_month = today.month - 1
            prev_year = today.year

        if prev_month == 12:
            next_month = 1
            next_year = prev_year + 1
        else:
            next_month = prev_month + 1
            next_year = prev_year

        days_in_prev_month = (
            date(next_year, next_month, 1) - date(prev_year, prev_month, 1)
        ).days
        days += days_in_prev_month

    if months < 0:
        years -= 1
        months += 12

    parts: list[str] = []

    if years > 0:
        parts.append(f"{years} г.")
    if months > 0:
        parts.append(f"{months} мес.")
    if days > 0:
        parts.append(f"{days} дн.")

    return " ".join(parts)


def get_owner_display(user) -> str:
    """Возвращает имя владельца для показа в интерфейсе."""
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    if full_name:
        return full_name
    return user.email


def is_moderator(user) -> bool:
    """Проверяет, является ли пользователь модератором."""
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name="Moderators").exists()


def can_view_pet(user, pet: Pet) -> bool:
    """Определяет, может ли пользователь смотреть карточку питомца."""
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False

    if is_moderator(user):
        return True

    if pet.owner_id == user.id:
        return True

    return pet.is_public


def can_edit_pet(user, pet: Pet) -> bool:
    """Определяет, может ли пользователь редактировать питомца."""
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False

    if is_moderator(user):
        return True

    return pet.owner_id == user.id


def get_next_repeat_datetime(event: Event) -> datetime | None:
    """Возвращает дату следующего повторения события."""
    if not event.repeat_after_days:
        return None
    return event.event_datetime + timedelta(days=event.repeat_after_days)


def get_no_handling_until(event: Event) -> datetime | None:
    """Возвращает дату окончания ограничения handling."""
    if not event.no_handling_days:
        return None
    return event.event_datetime + timedelta(days=event.no_handling_days)


def get_repeat_comment(event: Event) -> str:
    """Формирует строку следующего повторения события."""
    next_dt = get_next_repeat_datetime(event)
    if not next_dt:
        return ""

    if event.event_type == Event.EventType.FEEDING:
        prefix = "Следующее кормление"
    elif event.event_type == Event.EventType.CLEANING:
        prefix = "Следующая уборка"
    else:
        prefix = "Повторить"

    return f"{prefix}: {timezone.localtime(next_dt).strftime('%d.%m.%Y %H:%M')}"


def get_handling_comment(event: Event) -> str:
    """Формирует строку запрета handling."""
    until_dt = get_no_handling_until(event)
    if not until_dt:
        return ""

    return f"Не трогать до: {timezone.localtime(until_dt).strftime('%d.%m.%Y %H:%M')}"


def get_event_comment_lines(event: Event) -> list[str]:
    """Возвращает список строк комментария для таблиц."""
    lines: list[str] = []

    repeat_line = get_repeat_comment(event)
    handling_line = get_handling_comment(event)

    if repeat_line:
        lines.append(repeat_line)

    if handling_line:
        lines.append(handling_line)

    if event.comment:
        lines.append(event.comment)

    return lines


def get_event_comment_display(event: Event) -> str:
    """Возвращает текст комментария для таблиц."""
    return "\n".join(get_event_comment_lines(event))


def get_pet_latest_handling_event(pet: Pet) -> Event | None:
    """Возвращает последнее событие с ограничением handling."""
    return (
        pet.events.filter(no_handling_days__isnull=False)
        .order_by("-event_datetime")
        .first()
    )


def get_pet_no_handling_until(pet: Pet) -> datetime | None:
    """Возвращает дату, до которой питомца нельзя трогать."""
    event = get_pet_latest_handling_event(pet)
    if not event:
        return None
    return get_no_handling_until(event)


def pet_can_handle(pet: Pet) -> bool:
    """Можно ли сейчас трогать питомца."""
    until_dt = get_pet_no_handling_until(pet)
    if not until_dt:
        return True
    return timezone.now() >= until_dt


def pet_is_in_shedding(pet: Pet) -> bool:
    """Идёт ли сейчас линька с ограничением handling."""
    event = (
        pet.events.filter(
            event_type=Event.EventType.SHEDDING,
            no_handling_days__isnull=False,
        )
        .order_by("-event_datetime")
        .first()
    )

    if not event:
        return False

    until_dt = get_no_handling_until(event)
    if not until_dt:
        return False

    return timezone.now() < until_dt


def build_pet_card_context(pet: Pet, user) -> dict:
    """Собирает контекст карточки питомца."""
    return {
        "pet": pet,
        "pet_age_display": get_pet_age_display(pet.birth_date),
        "owner_display": get_owner_display(pet.owner),
        "can_edit_pet": can_edit_pet(user, pet),
        "can_view_owner": bool(user.is_authenticated and user.id != pet.owner_id),
        "can_view_owner_only_name": bool(user.is_authenticated and user.id != pet.owner_id),
        "is_owner": bool(user.is_authenticated and user.id == pet.owner_id),
        "can_handle": pet_can_handle(pet),
        "is_in_shedding": pet_is_in_shedding(pet),
    }


def build_event_row_context(event: Event) -> dict:
    """Собирает контекст строки события."""
    return {
        "event": event,
        "event_comment_display": get_event_comment_display(event),
    }