from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from users.services import (
    build_daily_care_notification_text,
    build_pet_notification_block,
    build_telegram_welcome_text,
    create_telegram_deep_link_for_user,
    disable_care_notifications,
    enable_care_notifications,
    generate_telegram_link_token,
    get_pet_tasks_for_today,
    get_telegram_updates,
    link_telegram_account_by_token,
    send_telegram_message,
    should_send_daily_notification_now,
    unlink_telegram_account,
)


@pytest.mark.django_db
def test_generate_telegram_link_token_returns_string():
    token = generate_telegram_link_token()
    assert isinstance(token, str)
    assert token
    assert len(token) <= 64


@pytest.mark.django_db
def test_create_telegram_deep_link_for_user_sets_token(user, settings):
    settings.TELEGRAM_BOT_USERNAME = "checkarium_test_bot"

    link = create_telegram_deep_link_for_user(user)
    user.refresh_from_db()

    assert "https://t.me/checkarium_test_bot?start=" in link
    assert user.telegram_link_token is not None
    assert user.telegram_link_token_created_at is not None


@pytest.mark.django_db
def test_enable_and_disable_care_notifications(user):
    enable_care_notifications(user)
    user.refresh_from_db()
    assert user.care_notifications_enabled is True

    disable_care_notifications(user)
    user.refresh_from_db()
    assert user.care_notifications_enabled is False


@pytest.mark.django_db
def test_unlink_telegram_account_clears_fields(user):
    user.telegram_id = 123456
    user.telegram_link_token = "token"
    user.telegram_link_token_created_at = timezone.now()
    user.telegram_linked_at = timezone.now()
    user.care_notifications_enabled = True
    user.last_care_notification_date = timezone.localdate()
    user.save()

    unlink_telegram_account(user)
    user.refresh_from_db()

    assert user.telegram_id is None
    assert user.telegram_link_token is None
    assert user.telegram_link_token_created_at is None
    assert user.telegram_linked_at is None
    assert user.care_notifications_enabled is False
    assert user.last_care_notification_date is None


@pytest.mark.django_db
def test_link_telegram_account_by_token_success(user):
    user.telegram_link_token = "valid-token"
    user.telegram_link_token_created_at = timezone.now()
    user.save()

    linked_user = link_telegram_account_by_token("valid-token", 999999)

    user.refresh_from_db()
    assert linked_user == user
    assert user.telegram_id == 999999
    assert user.telegram_link_token is None
    assert user.care_notifications_enabled is True


@pytest.mark.django_db
def test_link_telegram_account_by_token_raises_for_invalid_token():
    with pytest.raises(ValidationError, match="Ссылка недействительна или уже использована"):
        link_telegram_account_by_token("wrong-token", 123456)


@pytest.mark.django_db
def test_link_telegram_account_by_token_raises_if_chat_id_is_already_used(user, other_user):
    other_user.telegram_id = 111111
    other_user.save()

    user.telegram_link_token = "valid-token"
    user.telegram_link_token_created_at = timezone.now()
    user.save()

    with pytest.raises(ValidationError):
        link_telegram_account_by_token("valid-token", 111111)


@pytest.mark.django_db
def test_should_send_daily_notification_now_returns_false_without_telegram(user):
    user.telegram_id = None
    user.care_notifications_enabled = True
    user.save()

    assert should_send_daily_notification_now(user) is False


@pytest.mark.django_db
def test_should_send_daily_notification_now_returns_false_if_already_sent_today(user):
    user.telegram_id = 123456
    user.care_notifications_enabled = True
    user.last_care_notification_date = timezone.localdate()
    user.save()

    assert should_send_daily_notification_now(user) is False


@pytest.mark.django_db
def test_build_telegram_welcome_text_contains_profile_url(user, settings):
    settings.SITE_URL = "https://example.com"
    text = build_telegram_welcome_text(user)

    assert "https://example.com" in text
    assert user.email in text or user.first_name in text


@patch("users.services.requests.post")
@pytest.mark.django_db
def test_send_telegram_message(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = {"ok": True, "result": {"message_id": 1}}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = send_telegram_message(123456, "test")

    assert result["ok"] is True
    mock_post.assert_called_once()


@patch("users.services.requests.get")
@pytest.mark.django_db
def test_get_telegram_updates(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {"result": [{"update_id": 1}]}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = get_telegram_updates(offset=5)

    assert result == [{"update_id": 1}]
    mock_get.assert_called_once()


@pytest.mark.django_db
def test_get_pet_tasks_for_today_always_contains_change_water(user, pet):
    tasks = get_pet_tasks_for_today(pet, user)
    assert "поменяй воду" in tasks


@pytest.mark.django_db
def test_build_pet_notification_block_contains_pet_name_and_tasks(user, pet):
    text = build_pet_notification_block(pet, user)

    assert pet.name in text
    assert "Важные дела на сегодня" in text or "важных дел нет" in text.lower()


@pytest.mark.django_db
def test_build_daily_care_notification_text_contains_header_and_events_url(user, settings):
    settings.SITE_URL = "https://example.com"

    text = build_daily_care_notification_text(user)

    assert "Доброе утро" in text
    assert "https://example.com/pets/events/" in text


@pytest.mark.django_db
def test_build_daily_care_notification_text_for_user_without_pets(user, settings):
    settings.SITE_URL = "https://example.com"
    user.pets.all().delete()

    text = build_daily_care_notification_text(user)

    assert "У вас пока нет питомцев в системе." in text
    assert "https://example.com/pets/events/" in text
