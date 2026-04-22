import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_profile_detail_requires_login(client, user):
    response = client.get(reverse("users:profile_detail", kwargs={"pk": user.pk}))
    assert response.status_code == 302


@pytest.mark.django_db
def test_user_cannot_open_other_profile(other_auth_client, user):
    response = other_auth_client.get(reverse("users:profile_detail", kwargs={"pk": user.pk}))
    assert response.status_code == 403


@pytest.mark.django_db
def test_owner_can_open_own_profile(auth_client, user):
    response = auth_client.get(reverse("users:profile_detail", kwargs={"pk": user.pk}))
    assert response.status_code == 200


@pytest.mark.django_db
def test_telegram_enable_without_linked_telegram_redirects(auth_client, user):
    response = auth_client.post(reverse("users:telegram_enable", kwargs={"pk": user.pk}))
    assert response.status_code == 302


@pytest.mark.django_db
def test_telegram_connect_redirects_to_bot(auth_client, user, settings):
    settings.TELEGRAM_BOT_USERNAME = "checkarium_test_bot"

    response = auth_client.get(reverse("users:telegram_connect", kwargs={"pk": user.pk}))

    assert response.status_code == 302
    assert "https://t.me/checkarium_test_bot?start=" in response.url
