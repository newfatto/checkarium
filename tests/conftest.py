from datetime import timedelta

import pytest
from django.contrib.auth.models import Group
from django.utils import timezone

from pets.models import Event, Pet


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        email="user@example.com",
        password="testpass123",
        first_name="Катя",
        time_zone="UTC",
    )


@pytest.fixture
def other_user(django_user_model):
    return django_user_model.objects.create_user(
        email="other@example.com",
        password="testpass123",
        first_name="Оля",
        time_zone="UTC",
    )


@pytest.fixture
def moderator_user(django_user_model):
    user = django_user_model.objects.create_user(
        email="moderator@example.com",
        password="testpass123",
        first_name="Модератор",
        time_zone="UTC",
    )
    group, _ = Group.objects.get_or_create(name="Moderators")
    user.groups.add(group)
    return user


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def other_auth_client(client, other_user):
    client.force_login(other_user)
    return client


@pytest.fixture
def moderator_client(client, moderator_user):
    client.force_login(moderator_user)
    return client


@pytest.fixture
def pet(user):
    return Pet.objects.create(
        owner=user,
        name="Куку",
        animal_type=Pet.AnimalType.SNAKE,
        species_name="Маисовый полоз",
        sex=Pet.Sex.UNKNOWN,
        weight_grams=20,
        length_cm=35,
        is_public=True,
    )


@pytest.fixture
def private_pet(user):
    return Pet.objects.create(
        owner=user,
        name="Тайный",
        animal_type=Pet.AnimalType.SNAKE,
        species_name="Королевский питон",
        sex=Pet.Sex.UNKNOWN,
        is_public=False,
    )


@pytest.fixture
def other_pet(other_user):
    return Pet.objects.create(
        owner=other_user,
        name="Чужой",
        animal_type=Pet.AnimalType.LIZARD,
        species_name="Эублефар",
        sex=Pet.Sex.UNKNOWN,
        is_public=True,
    )


@pytest.fixture
def feeding_event(user, pet):
    return Event.objects.create(
        owner=user,
        pet=pet,
        event_type=Event.EventType.FEEDING,
        event_datetime=timezone.now() - timedelta(days=2),
        repeat_after_days=7,
        no_handling_days=2,
        comment="После кормления не трогать",
    )


@pytest.fixture
def measurement_event(user, pet):
    return Event.objects.create(
        owner=user,
        pet=pet,
        event_type=Event.EventType.MEASUREMENT,
        event_datetime=timezone.now() - timedelta(days=1),
        weight_grams=25,
        length_cm=40,
        comment="Контрольное измерение",
    )


@pytest.fixture
def shedding_event(user, pet):
    return Event.objects.create(
        owner=user,
        pet=pet,
        event_type=Event.EventType.SHEDDING,
        event_datetime=timezone.now() - timedelta(hours=12),
        no_handling_days=2,
        comment="Линька",
    )