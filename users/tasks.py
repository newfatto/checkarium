from celery import shared_task
from .timezone_services import get_user_local_now

from .models import CustomUser
from .services import (
    build_daily_care_notification_text,
    send_telegram_message,
    should_send_daily_notification_now,
)


@shared_task
def send_daily_care_notifications() -> None:
    """Отправляет ежедневные уведомления пользователям, у которых локально 07:00."""
    users = CustomUser.objects.filter(
        care_notifications_enabled=True,
        telegram_id__isnull=False,
    )

    for user in users:
        if not should_send_daily_notification_now(user):
            continue

        text = build_daily_care_notification_text(user)
        send_telegram_message(chat_id=user.telegram_id, text=text)

        user.last_care_notification_date = get_user_local_now(user).date()
        user.save(update_fields=["last_care_notification_date"])