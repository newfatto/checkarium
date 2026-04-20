from getpass import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    """Кастомная команда для создания суперпользователя."""

    help = "Создаёт суперпользователя с авторизацией по email."

    def handle(self, *args: tuple, **options: dict) -> None:
        """
        Запустить команду создания суперпользователя.

        :param args: Позиционные аргументы команды.
        :param options: Именованные аргументы команды.
        :return: None.
        """
        email = input("Введите email: ").strip()
        first_name = input("Введите имя: ").strip()
        last_name = input("Введите фамилию: ").strip()
        password = getpass("Введите пароль: ").strip()
        password_repeat = getpass("Повторите пароль: ").strip()

        if not email:
            raise CommandError("Email обязателен.")

        if not first_name:
            raise CommandError("Имя обязательно.")

        if password != password_repeat:
            raise CommandError("Пароли не совпадают.")

        if User.objects.filter(email=email).exists():
            raise CommandError("Пользователь с таким email уже существует.")

        User.objects.create_superuser(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )

        self.stdout.write(self.style.SUCCESS("Суперпользователь успешно создан."))
