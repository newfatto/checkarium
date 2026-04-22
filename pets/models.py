from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from users.validators import validate_image_file


class Pet(models.Model):
    """Модель питомца (рептилии или другого экзотического животного)."""

    class AnimalType(models.TextChoices):
        SNAKE = "snake", "Змея"
        LIZARD = "lizard", "Ящерица"
        TURTLE = "turtle", "Черепаха"
        FROG = "frog", "Лягушка"
        SPIDER = "spider", "Паук"
        SCORPION = "scorpion", "Скорпион"
        OTHER = "other", "Иное"

    class Sex(models.TextChoices):
        MALE = "male", "Самец"
        FEMALE = "female", "Самка"
        UNKNOWN = "unknown", "Неизвестен"

    class Status(models.TextChoices):
        ACTIVE = "active", "Активен"
        ARCHIVED = "archived", "В архиве"
        DECEASED = "deceased", "Умер"
        REHOMED = "rehomed", "Передан"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pets",
        verbose_name="Владелец",
    )

    name = models.CharField(max_length=100, verbose_name="Имя питомца")

    animal_type = models.CharField(
        max_length=20,
        choices=AnimalType.choices,
        verbose_name="Тип животного",
    )

    species_name = models.CharField(
        max_length=150,
        verbose_name="Вид",
        help_text="Например: Маисовый полоз",
    )

    morph = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Морфа / окрас",
    )

    sex = models.CharField(
        max_length=10,
        choices=Sex.choices,
        default=Sex.UNKNOWN,
        verbose_name="Пол",
    )

    birth_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Дата рождения",
    )

    acquired_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Дата начала владения",
        help_text="Укажите, когда питомец появился у вас",
    )

    weight_grams = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Вес (г)",
        validators=[MinValueValidator(1), MaxValueValidator(200000)],
    )

    length_cm = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Длина (см)",
        validators=[MinValueValidator(1), MaxValueValidator(500)],
    )

    photo = models.ImageField(
        upload_to="pets/photos/",
        blank=True,
        null=True,
        verbose_name="Фото",
        validators=[validate_image_file],
    )

    feeding_notes = models.TextField(
        blank=True,
        verbose_name="Чем кормить",
        help_text="Например: мышь-голыш, крысёныш, сверчки, тараканы, овощная смесь",
    )

    notes = models.TextField(blank=True, verbose_name="Комментарий")

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Статус",
    )

    is_public = models.BooleanField(
        default=True,
        verbose_name="Показывать питомца всем",
        help_text="Если включено, карточка будет видна на главной странице и авторизованным пользователям",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Нормализует текстовые поля и проверяет логическую корректность дат."""
        super().clean()

        if self.name:
            self.name = self.name.strip()

        if self.species_name:
            self.species_name = self.species_name.strip()

        if self.morph:
            self.morph = self.morph.strip()

        if self.name == "":
            raise ValidationError({"name": "Имя питомца не может быть пустым."})

        if self.species_name == "":
            raise ValidationError({"species_name": "Вид не может быть пустым."})

        if self.birth_date and self.birth_date > timezone.localdate():
            raise ValidationError({"birth_date": "Дата рождения не может быть в будущем."})

        if self.acquired_date and self.acquired_date > timezone.localdate():
            raise ValidationError({"acquired_date": "Дата начала владения не может быть в будущем."})

        if self.birth_date and self.acquired_date and self.acquired_date < self.birth_date:
            raise ValidationError({"acquired_date": "Дата начала владения не может быть раньше даты рождения."})

    def __str__(self) -> str:
        """Формирует читаемое строковое представление питомца."""
        return f"{self.name} ({self.species_name})"

    def get_absolute_url(self) -> str:
        """Возвращает URL страницы детального просмотра питомца."""
        return reverse("pets:pet_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        """Запускает полную валидацию модели перед сохранением."""
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "питомец"
        verbose_name_plural = "питомцы"


class Event(models.Model):
    """Модель события ухода или наблюдения, связанного с конкретным питомцем."""

    class EventType(models.TextChoices):
        FEEDING = "feeding", "Кормление"
        MEASUREMENT = "measurement", "Измерение"
        CLEANING = "cleaning", "Уборка"
        SHEDDING = "shedding", "Линька"
        CUSTOM = "custom", "Другое"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Владелец",
    )

    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Питомец",
    )

    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        verbose_name="Тип события",
    )

    title = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Название события",
    )

    event_datetime = models.DateTimeField(
        verbose_name="Дата и время события",
    )

    comment = models.TextField(
        blank=True,
        verbose_name="Комментарий",
    )

    repeat_after_days = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Повторить через (дней)",
        validators=[MinValueValidator(1), MaxValueValidator(3650)],
    )

    no_handling_days = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Нельзя трогать (суток)",
        validators=[MaxValueValidator(365)],
    )

    weight_grams = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Вес (г)",
        validators=[MinValueValidator(1), MaxValueValidator(200000)],
    )

    length_cm = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Длина (см)",
        validators=[MinValueValidator(1), MaxValueValidator(500)],
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Проверяет бизнес-правила события и согласованность его полей."""
        super().clean()

        if self.title:
            self.title = self.title.strip()

        if self.comment:
            self.comment = self.comment.strip()

        if self.event_type == self.EventType.CUSTOM and not self.title:
            raise ValidationError({"title": "Для пользовательского события укажите название."})

        if self.event_type != self.EventType.CUSTOM and self.title:
            raise ValidationError({"title": "Название заполняется только для события 'Другое'."})

        if self.event_type == self.EventType.MEASUREMENT:
            if self.weight_grams is None and self.length_cm is None:
                raise ValidationError("Для измерения укажите вес или длину.")

        if self.event_type != self.EventType.MEASUREMENT:
            if self.weight_grams is not None or self.length_cm is not None:
                raise ValidationError("Вес и длина указываются только для события измерения.")

        if self.event_type == self.EventType.SHEDDING and self.repeat_after_days:
            raise ValidationError({"repeat_after_days": "Для линьки повторение обычно не задаётся."})

        if self.pet_id and self.owner_id and self.pet.owner_id != self.owner_id:
            raise ValidationError({"pet": "Питомец должен принадлежать выбранному владельцу."})

        if self.event_datetime and self.event_datetime > timezone.now():
            raise ValidationError({"event_datetime": "Дата и время события не могут быть в будущем."})

    def save(self, *args, **kwargs):
        """Сохраняет событие и обновляет параметры питомца, если это событие измерения."""

        self.full_clean()
        super().save(*args, **kwargs)

        if self.event_type == self.EventType.MEASUREMENT:
            pet: Pet = self.pet
            fields_to_update = []

            if self.weight_grams is not None:
                pet.weight_grams = self.weight_grams
                fields_to_update.append("weight_grams")

            if self.length_cm is not None:
                pet.length_cm = self.length_cm
                fields_to_update.append("length_cm")

            if fields_to_update:
                pet.save(update_fields=fields_to_update)

    def get_absolute_url(self) -> str:
        """Возвращает URL страницы детального просмотра события."""
        return reverse("pets:event_detail", kwargs={"pk": self.pk})

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "событие"
        verbose_name_plural = "события"
