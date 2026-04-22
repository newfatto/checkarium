import pytest
from django.core.exceptions import ValidationError


@pytest.mark.django_db
def test_create_user_normalizes_email(django_user_model):
    user = django_user_model.objects.create_user(
        email="Test@Example.COM",
        password="testpass123",
        first_name="Катя",
        time_zone="UTC",
    )
    assert user.email == "Test@example.com"


@pytest.mark.django_db
def test_create_user_without_email_raises_error(django_user_model):
    with pytest.raises(ValueError):
        django_user_model.objects.create_user(
            email="",
            password="testpass123",
            first_name="Катя",
            time_zone="UTC",
        )


@pytest.mark.django_db
def test_user_str_returns_email(user):
    assert str(user) == user.email


@pytest.mark.django_db
def test_user_clean_disallows_notifications_without_telegram(user):
    user.care_notifications_enabled = True
    user.telegram_id = None

    with pytest.raises(ValidationError):
        user.full_clean()
