from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from pets.models import Event, Pet


@pytest.mark.django_db
def test_pet_birth_date_cannot_be_in_future(user):
    pet = Pet(
        owner=user,
        name="Куку",
        animal_type=Pet.AnimalType.SNAKE,
        species_name="Маисовый полоз",
        birth_date=timezone.localdate() + timedelta(days=1),
    )

    with pytest.raises(ValidationError):
        pet.full_clean()


@pytest.mark.django_db
def test_pet_acquired_date_cannot_be_before_birth_date(user):
    pet = Pet(
        owner=user,
        name="Куку",
        animal_type=Pet.AnimalType.SNAKE,
        species_name="Маисовый полоз",
        birth_date=timezone.localdate(),
        acquired_date=timezone.localdate() - timedelta(days=1),
    )

    with pytest.raises(ValidationError):
        pet.full_clean()


@pytest.mark.django_db
def test_custom_event_requires_title(user, pet):
    event = Event(
        owner=user,
        pet=pet,
        event_type=Event.EventType.CUSTOM,
        event_datetime=timezone.now(),
        title="",
    )

    with pytest.raises(ValidationError):
        event.full_clean()


@pytest.mark.django_db
def test_measurement_event_requires_weight_or_length(user, pet):
    event = Event(
        owner=user,
        pet=pet,
        event_type=Event.EventType.MEASUREMENT,
        event_datetime=timezone.now(),
    )

    with pytest.raises(ValidationError):
        event.full_clean()


@pytest.mark.django_db
def test_event_datetime_cannot_be_in_future(user, pet):
    event = Event(
        owner=user,
        pet=pet,
        event_type=Event.EventType.FEEDING,
        event_datetime=timezone.now() + timedelta(hours=1),
    )

    with pytest.raises(ValidationError):
        event.full_clean()


@pytest.mark.django_db
def test_measurement_event_updates_pet_measurements(user, pet):
    Event.objects.create(
        owner=user,
        pet=pet,
        event_type=Event.EventType.MEASUREMENT,
        event_datetime=timezone.now(),
        weight_grams=44,
        length_cm=55,
    )

    pet.refresh_from_db()
    assert pet.weight_grams == 44
    assert pet.length_cm == 55


@pytest.mark.django_db
def test_event_pet_must_belong_to_owner(user, other_pet):
    event = Event(
        owner=user,
        pet=other_pet,
        event_type=Event.EventType.FEEDING,
        event_datetime=timezone.now(),
    )

    with pytest.raises(ValidationError):
        event.full_clean()
