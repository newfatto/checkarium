from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from pets.models import Event
from pets.services import (
    _format_signed_diff,
    get_event_comment_display,
    get_measurement_comment_lines,
    get_next_repeat_datetime,
    get_no_handling_until,
    get_pet_age_display,
    get_upcoming_pet_tasks,
    pet_can_handle,
    pet_is_in_shedding,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("birth_date", "expected"),
    [
        (None, ""),
        (date.today() + timedelta(days=1), ""),
    ],
)
def test_get_pet_age_display_empty_cases(birth_date, expected):
    assert get_pet_age_display(birth_date) == expected


@pytest.mark.django_db
def test_get_pet_age_display_for_small_age():
    birth_date = timezone.localdate() - timedelta(days=10)
    assert get_pet_age_display(birth_date) == "10 дн."


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (5, "+5"),
        (-3, "-3"),
        (Decimal("1.5"), "+1.5"),
        (Decimal("-2.5"), "-2.5"),
    ],
)
def test_format_signed_diff(value, expected):
    assert _format_signed_diff(value) == expected


@pytest.mark.django_db
def test_get_next_repeat_datetime(feeding_event):
    next_dt = get_next_repeat_datetime(feeding_event)
    assert next_dt == feeding_event.event_datetime + timedelta(days=feeding_event.repeat_after_days)


@pytest.mark.django_db
def test_get_no_handling_until(feeding_event):
    until_dt = get_no_handling_until(feeding_event)
    assert until_dt == feeding_event.event_datetime + timedelta(days=feeding_event.no_handling_days)


@pytest.mark.django_db
def test_get_measurement_comment_lines_without_previous(measurement_event):
    lines = get_measurement_comment_lines(measurement_event)

    assert any("Вес:" in line for line in lines)
    assert any("Длина:" in line for line in lines)


@pytest.mark.django_db
def test_get_measurement_comment_lines_with_previous(user, pet):
    Event.objects.create(
        owner=user,
        pet=pet,
        event_type=Event.EventType.MEASUREMENT,
        event_datetime=timezone.now() - timedelta(days=2),
        weight_grams=20,
        length_cm=35,
    )
    current_event = Event.objects.create(
        owner=user,
        pet=pet,
        event_type=Event.EventType.MEASUREMENT,
        event_datetime=timezone.now() - timedelta(days=1),
        weight_grams=25,
        length_cm=40,
    )

    lines = get_measurement_comment_lines(current_event)

    assert any("(+5 г)" in line for line in lines)
    assert any("(+5 см)" in line for line in lines)


@pytest.mark.django_db
def test_pet_can_handle_false_when_no_handling_is_active(shedding_event, pet):
    assert pet_can_handle(pet) is False


@pytest.mark.django_db
def test_pet_is_in_shedding_true_when_shedding_is_active(shedding_event, pet):
    assert pet_is_in_shedding(pet) is True


@pytest.mark.django_db
def test_get_upcoming_pet_tasks_returns_sorted_tasks(user, pet):
    Event.objects.create(
        owner=user,
        pet=pet,
        event_type=Event.EventType.CLEANING,
        event_datetime=timezone.now() - timedelta(days=1),
        repeat_after_days=3,
    )
    Event.objects.create(
        owner=user,
        pet=pet,
        event_type=Event.EventType.FEEDING,
        event_datetime=timezone.now() - timedelta(days=1),
        repeat_after_days=1,
    )

    tasks = get_upcoming_pet_tasks(pet)

    assert len(tasks) == 2
    assert tasks[0].startswith("Покормить")
    assert tasks[1].startswith("Убраться")


@pytest.mark.django_db
def test_get_event_comment_display_contains_comment_parts(feeding_event):
    text = get_event_comment_display(feeding_event)

    assert "Следующее кормление" in text
    assert "Не трогать до:" in text
    assert "После кормления не трогать" in text