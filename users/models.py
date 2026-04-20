from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError

from django.core.validators import EmailValidator
from .validators import (
    validate_image_file,
    validate_person_name,
    validate_phone_number,
    validate_time_zone,
)


class CustomUserManager(BaseUserManager):
    """Менеджер для кастомной модели пользователя с авторизацией по email."""

    use_in_migrations = True

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: object,
    ) -> "CustomUser":
        """
        Создать и сохранить обычного пользователя.

        :param email: Email пользователя.
        :param password: Пароль пользователя.
        :param extra_fields: Дополнительные поля модели.
        :return: Экземпляр CustomUser.
        """
        if not email:
            raise ValueError("У пользователя должен быть указан email.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: object,
    ) -> "CustomUser":
        """
        Создать и сохранить суперпользователя.

        :param email: Email суперпользователя.
        :param password: Пароль суперпользователя.
        :param extra_fields: Дополнительные поля модели.
        :return: Экземпляр CustomUser.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("У суперпользователя is_staff должен быть True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("У суперпользователя is_superuser должен быть True.")

        return self.create_user(email=email, password=password, **extra_fields)


class CustomUser(AbstractUser):
    """Кастомная модель пользователя с авторизацией по email."""

    username = None

    email = models.EmailField(
        unique=True,
        validators=[EmailValidator(message="Введите корректный email.")],
        verbose_name="Email",
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name="Имя",
        validators=[validate_person_name],
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Фамилия",
        validators=[validate_person_name],
    )
    city = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Город",
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Телефон",
        validators=[validate_phone_number],
    )
    avatar = models.ImageField(
        upload_to="users/avatars/",
        blank=True,
        null=True,
        verbose_name="Аватар",
        validators=[validate_image_file],
    )
    bio = models.TextField(
        blank=True,
        verbose_name="О себе",
        help_text="Краткий комментарий пользователя о себе.",
    )
    telegram_id = models.BigIntegerField(
        blank=True,
        null=True,
        unique=True,
        verbose_name="Telegram ID",
        help_text="Заполняется автоматически через Telegram-бота.",
    )

    telegram_link_token = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        verbose_name="Токен привязки Telegram",
        help_text="Одноразовый токен для привязки Telegram через бота.",
    )

    telegram_link_token_created_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Время создания токена привязки Telegram",
    )

    telegram_linked_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Время привязки Telegram",
    )

    care_notifications_enabled = models.BooleanField(
        default=False,
        verbose_name="Уведомления об уходе",
        help_text="Получать ежедневные уведомления в Telegram.",
    )

    last_care_notification_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Дата последнего уведомления об уходе",
    )

    time_zone = models.CharField(
        max_length=64,
        default="UTC",
        verbose_name="Часовой пояс",
        validators=[validate_time_zone],
    )

    def clean(self) -> None:
        """Нормализует и проверяет данные пользователя."""
        super().clean()

        if self.email:
            self.email = self.email.strip().lower()

        if self.first_name:
            self.first_name = self.first_name.strip()

        if self.last_name:
            self.last_name = self.last_name.strip()

        if self.phone_number:
            self.phone_number = self.phone_number.strip()

        if self.care_notifications_enabled and not self.telegram_id:
            raise ValidationError({
                "care_notifications_enabled": "Нельзя включить уведомления без привязанного Telegram."
            })

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = CustomUserManager()

    def __str__(self) -> str:
        """
        Вернуть строковое представление пользователя.

        :return: Email пользователя.
        """
        return self.email

    def get_absolute_url(self) -> str:
        """
        Вернуть URL страницы профиля пользователя.

        :return: URL профиля.
        """
        return reverse("users:profile_detail", kwargs={"pk": self.pk})

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
