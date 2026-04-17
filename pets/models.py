from django.conf import settings
from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone


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

    name = models.CharField(
        max_length=100,
        verbose_name="Имя животного"
    )

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
        help_text="Укажите, когда животное появилось у вас",
    )

    weight_grams = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Вес (г)",
    )
    length_cm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Длина (см)",
    )

    photo = models.ImageField(
        upload_to="pets/photos/",
        blank=True,
        null=True,
        verbose_name="Фото",
    )

    notes = models.TextField(
        blank=True,
        verbose_name="Комментарий"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Статус",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def clean(self):
        """ Проверяет корректность дат."""
        if self.birth_date and self.birth_date > timezone.localdate():
            raise ValidationError({"birth_date": "Дата рождения не может быть в будущем."})
        if self.acquired_date and self.acquired_date > timezone.localdate():
            raise ValidationError({"acquired_date": "Дата начала владения не может быть в будущем."})
        if self.birth_date and self.acquired_date and self.acquired_date < self.birth_date:
            raise ValidationError({"acquired_date": "Дата начала владения не может быть раньше даты рождения."})

    def __str__(self) -> str:
        return f"{self.name} ({self.species_name})"

    def get_absolute_url(self) -> str:
        return reverse("pets:pet_detail", kwargs={"pk": self.pk})

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "питомец"
        verbose_name_plural = "питомцы"


class Event(models.Model):
    """Событие, связанное с питомцем."""

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
        verbose_name="Владелец"
    )

    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Животное",
    )

    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        verbose_name="Тип события",
    )

    title = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Название события"
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
        verbose_name="Повторить через (дней)"
    )

    no_handling_days = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Нельзя трогать (суток)"
    )

    weight_grams = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Вес (г)"
    )

    length_cm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Длина (см)"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def clean(self):
        """ Проверяет тип события:
        Требует название для пользовательского события.
        Требует при измерении указывать как минимум вес или длину.
        Проверяет, что питомец принадлежит владельцу.
        """

        if self.event_type == self.EventType.CUSTOM and not self.title:
            raise ValidationError({
                "title": "Для пользовательского события укажите название."
            })

        if self.event_type == self.EventType.MEASUREMENT:
            if self.weight_grams is None and self.length_cm is None:
                raise ValidationError("Для измерения укажите вес или длину.")

        if self.pet_id and self.owner_id and self.pet.owner_id != self.owner_id:
            raise ValidationError({"pet": "Питомец должен принадлежать выбранному владельцу."})

        if self.event_date and self.event_date > timezone.now():
            raise ValidationError({"event_date": "Дата и время события не могут быть в будущем."})


    def save(self, *args, **kwargs):
        """При сохранении измерения обновляем Pet."""
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

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "событие"
        verbose_name_plural = "события"