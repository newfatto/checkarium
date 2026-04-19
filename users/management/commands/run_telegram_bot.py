from django.conf import settings
from django.core.management.base import BaseCommand

from users.services import (
    get_telegram_updates,
    link_telegram_account_by_token,
    send_telegram_message,
)


class Command(BaseCommand):
    """Запускает Telegram-бота в режиме long polling."""

    help = "Run Telegram bot for linking Telegram accounts."

    def handle(self, *args, **options) -> None:
        if not settings.TELEGRAM_BOT_TOKEN:
            self.stdout.write(self.style.ERROR("TELEGRAM_BOT_TOKEN не задан."))
            return

        if not settings.TELEGRAM_BOT_USERNAME:
            self.stdout.write(self.style.ERROR("TELEGRAM_BOT_USERNAME не задан."))
            return

        self.stdout.write(self.style.SUCCESS("Telegram bot started."))
        offset: int | None = None

        while True:
            updates = get_telegram_updates(offset=offset)

            for update in updates:
                offset = update["update_id"] + 1

                message = update.get("message")
                if not message:
                    continue

                text = message.get("text", "").strip()
                chat = message.get("chat", {})
                chat_id = chat.get("id")

                if not text.startswith("/start"):
                    continue

                parts = text.split(maxsplit=1)
                token = parts[1].strip() if len(parts) > 1 else ""

                if not token or chat_id is None:
                    send_telegram_message(
                        chat_id=chat_id,
                        text="Откройте бота по кнопке из профиля Checkarium.",
                    )
                    continue

                user = link_telegram_account_by_token(token=token, chat_id=chat_id)

                if user is None:
                    send_telegram_message(
                        chat_id=chat_id,
                        text="Ссылка для подключения недействительна или уже использована.",
                    )
                    continue

                send_telegram_message(
                    chat_id=chat_id,
                    text=(
                        f"Привет, {user.first_name or user.email}!\n\n"
                        "Telegram успешно подключён.\n"
                        "Ежедневные уведомления об уходе включены."
                    ),
                )