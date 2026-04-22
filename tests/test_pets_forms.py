import pytest
from django.utils import timezone

from pets.forms import CustomEventForm, FeedingEventForm, PetForm


@pytest.mark.django_db
def test_pet_form_strips_name_and_species(user):
    form = PetForm(
        data={
            "name": "  Куку  ",
            "is_public": True,
            "animal_type": "snake",
            "species_name": "  Маисовый полоз  ",
            "morph": "  Амел  ",
            "sex": "unknown",
            "birth_date": "",
            "acquired_date": "",
            "weight_grams": 20,
            "length_cm": 35,
            "feeding_notes": "",
            "notes": "",
        }
    )

    assert form.is_valid()
    assert form.cleaned_data["name"] == "Куку"
    assert form.cleaned_data["species_name"] == "Маисовый полоз"
    assert form.cleaned_data["morph"] == "Амел"


@pytest.mark.django_db
def test_event_form_disallows_other_users_pet(user, other_pet):
    form = FeedingEventForm(
        data={
            "pet": other_pet.pk,
            "event_datetime": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            "no_handling_days": 1,
            "repeat_after_days": 7,
            "comment": "test",
        },
        user=user,
        is_moderator=False,
    )

    assert form.is_valid() is False
    assert "pet" in form.errors


@pytest.mark.django_db
def test_custom_event_form_strips_title_and_comment(user, pet):
    form = CustomEventForm(
        data={
            "pet": pet.pk,
            "title": "  Проверить лампу  ",
            "event_datetime": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            "repeat_after_days": "",
            "no_handling_days": "",
            "comment": "  Сделать сегодня  ",
        },
        initial={"event_type": "custom"},
        user=user,
        is_moderator=False,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["title"] == "Проверить лампу"
    assert form.cleaned_data["comment"] == "Сделать сегодня"
