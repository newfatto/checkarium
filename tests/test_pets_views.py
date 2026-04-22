import pytest
from django.urls import reverse
from django.utils import timezone

from pets.models import Event, Pet


@pytest.mark.django_db
def test_pet_list_shows_only_users_pets(auth_client, user, other_pet):
    Pet.objects.create(
        owner=user,
        name="Мой",
        animal_type=Pet.AnimalType.SNAKE,
        species_name="Маисовый полоз",
    )

    response = auth_client.get(reverse("pets:pet_list"))

    assert response.status_code == 200
    pets = response.context["pets"]
    assert all(p.owner == user for p in pets)


@pytest.mark.django_db
def test_private_pet_is_forbidden_for_other_user(other_auth_client, private_pet):
    response = other_auth_client.get(reverse("pets:pet_detail", kwargs={"pk": private_pet.pk}))
    assert response.status_code == 403


@pytest.mark.django_db
def test_pet_create_sets_owner(auth_client, user):
    response = auth_client.post(
        reverse("pets:pet_create"),
        data={
            "name": "Новый",
            "is_public": True,
            "animal_type": "snake",
            "species_name": "Маисовый полоз",
            "morph": "",
            "sex": "unknown",
            "birth_date": "",
            "acquired_date": "",
            "weight_grams": 10,
            "length_cm": 20,
            "feeding_notes": "",
            "notes": "",
        },
    )

    assert response.status_code == 302
    pet = Pet.objects.get(name="Новый")
    assert pet.owner == user


@pytest.mark.django_db
def test_event_list_filters_by_event_type(auth_client, user, pet):
    Event.objects.create(
        owner=user,
        pet=pet,
        event_type=Event.EventType.FEEDING,
        event_datetime=timezone.now(),
    )
    Event.objects.create(
        owner=user,
        pet=pet,
        event_type=Event.EventType.CLEANING,
        event_datetime=timezone.now(),
    )

    response = auth_client.get(reverse("pets:event_list"), data={"event_type": [Event.EventType.FEEDING]})

    assert response.status_code == 200
    events = response.context["events"]
    assert all(event.event_type == Event.EventType.FEEDING for event in events)


@pytest.mark.django_db
def test_event_create_for_user_uses_request_user_as_owner(auth_client, user, pet):
    response = auth_client.post(
        reverse("pets:event_create", kwargs={"event_type": "feeding"}),
        data={
            "pet": pet.pk,
            "event_type": "feeding",
            "event_datetime": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            "no_handling_days": 1,
            "repeat_after_days": 7,
            "comment": "Покормить",
        },
    )

    assert response.status_code == 302
    event = Event.objects.latest("id")
    assert event.owner == user
    assert event.pet == pet
    assert event.event_type == Event.EventType.FEEDING
