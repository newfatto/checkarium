import pytest

from users.forms import CustomUserCreationForm, CustomUserUpdateForm


@pytest.mark.django_db
def test_user_creation_form_rejects_duplicate_email(user):
    form = CustomUserCreationForm(
        data={
            "email": user.email.upper(),
            "first_name": "Новая",
            "time_zone": "UTC+00:00",
            "password1": "testpass12345",
            "password2": "testpass12345",
        }
    )

    assert form.is_valid() is False
    assert "email" in form.errors


@pytest.mark.django_db
def test_user_update_form_rejects_duplicate_email(user, other_user):
    form = CustomUserUpdateForm(
        data={
            "email": other_user.email.upper(),
            "first_name": "Катя",
            "last_name": "",
            "city": "",
            "phone_number": "",
            "time_zone": "UTC+00:00",
            "bio": "",
        },
        instance=user,
    )

    assert form.is_valid() is False
    assert "email" in form.errors


@pytest.mark.django_db
def test_user_update_form_strips_spaces(user):
    form = CustomUserUpdateForm(
        data={
            "email": "new@example.com",
            "first_name": "  Катя  ",
            "last_name": "  Иванова  ",
            "city": "",
            "phone_number": "  +79991234567  ",
            "time_zone": "UTC+00:00",
            "bio": "",
        },
        instance=user,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["first_name"] == "Катя"
    assert form.cleaned_data["last_name"] == "Иванова"
    assert form.cleaned_data["phone_number"] == "+79991234567"