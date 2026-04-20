from django import forms
from django.utils import timezone

from users.timezone_services import get_user_tzinfo

from .models import Event, Pet

# ---------------- PET ----------------


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = [
            "name",
            "is_public",
            "animal_type",
            "species_name",
            "morph",
            "sex",
            "birth_date",
            "acquired_date",
            "weight_grams",
            "length_cm",
            "photo",
            "feeding_notes",
            "notes",
        ]
        labels = {
            "name": "Имя",
            "animal_type": "Тип животного",
            "species_name": "Вид",
            "morph": "Морфа / окрас",
            "sex": "Пол",
            "birth_date": "Дата рождения",
            "acquired_date": "Дата появления у вас",
            "weight_grams": "Вес (г)",
            "length_cm": "Длина (см)",
            "photo": "Фото",
            "is_public": "Показывать питомца всем",
            "feeding_notes": "Чем кормить",
            "notes": "Заметки",
        }
        help_texts = {
            "is_public": "Если включено, питомец будет показан на главной странице и авторизованным пользователям.",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "animal_type": forms.Select(attrs={"class": "form-select"}),
            "species_name": forms.TextInput(attrs={"class": "form-control"}),
            "morph": forms.TextInput(attrs={"class": "form-control"}),
            "sex": forms.Select(attrs={"class": "form-select"}),
            "birth_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date", "class": "form-control"},
            ),
            "acquired_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date", "class": "form-control"},
            ),
            "weight_grams": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Вес в граммах"}),
            "length_cm": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Длина в сантиметрах", "step": "0.1"}
            ),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "is_public": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "feeding_notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Например: мыши, крысята, сверчки",
                }
            ),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["birth_date"].input_formats = ["%Y-%m-%d"]
        self.fields["acquired_date"].input_formats = ["%Y-%m-%d"]

    def clean_pet(self):
        """Проверяет, что питомец доступен пользователю."""
        pet = self.cleaned_data.get("pet")
        if self.user and pet and pet.owner_id != self.user.id:
            raise forms.ValidationError("Нельзя создать событие для чужого питомца.")
        return pet

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_species_name(self):
        return self.cleaned_data["species_name"].strip()

    def clean_morph(self):
        return self.cleaned_data.get("morph", "").strip()


# ---------------- BASE EVENT ----------------


class BaseEventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = [
            "pet",
            "event_type",
            "title",
            "event_datetime",
            "comment",
            "repeat_after_days",
            "no_handling_days",
            "weight_grams",
            "length_cm",
        ]
        labels = {
            "pet": "Животное",
            "event_type": "Тип события",
            "title": "Название",
            "event_datetime": "Дата и время",
            "comment": "Комментарий",
            "repeat_after_days": "Повторить через (дней)",
            "no_handling_days": "Нельзя трогать (дней)",
            "weight_grams": "Вес (г)",
            "length_cm": "Длина (см)",
        }
        widgets = {
            "pet": forms.Select(attrs={"class": "form-select"}),
            "event_type": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "event_datetime": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M",
            ),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "repeat_after_days": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Например: 7"}),
            "no_handling_days": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Например: 2"}),
            "weight_grams": forms.NumberInput(attrs={"class": "form-control"}),
            "length_cm": forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        is_moderator = kwargs.pop("is_moderator", False)
        self.user = user
        super().__init__(*args, **kwargs)

        self.fields["event_datetime"].input_formats = ["%Y-%m-%dT%H:%M"]

        if user and not is_moderator:
            self.fields["pet"].queryset = Pet.objects.filter(owner=user)

        self.fields["event_type"].disabled = True

    def clean_event_datetime(self):
        """Преобразует введённое пользователем время в aware datetime его часового пояса."""
        event_datetime = self.cleaned_data.get("event_datetime")

        if not event_datetime or not self.user:
            return event_datetime

        user_tz = get_user_tzinfo(self.user.time_zone)

        if timezone.is_aware(event_datetime):
            naive_local_dt = timezone.make_naive(
                event_datetime,
                timezone.get_current_timezone(),
            )
        else:
            naive_local_dt = event_datetime

        return timezone.make_aware(naive_local_dt, user_tz)

    def clean_title(self):
        return self.cleaned_data.get("title", "").strip()

    def clean_comment(self):
        return self.cleaned_data.get("comment", "").strip()


# ---------------- SPECIFIC FORMS ----------------


class FeedingEventForm(BaseEventForm):
    """Форма для создания события 'Кормление'"""

    class Meta(BaseEventForm.Meta):
        fields = [
            "pet",
            "event_type",
            "event_datetime",
            "no_handling_days",
            "repeat_after_days",
            "comment",
        ]
        help_texts = {
            "no_handling_days": "Сколько дней нельзя брать животное после кормления",
            "repeat_after_days": "Когда нужно следующее кормление",
        }


class SheddingEventForm(BaseEventForm):
    """Форма для создания события 'Линька'"""

    class Meta(BaseEventForm.Meta):
        fields = [
            "pet",
            "event_type",
            "event_datetime",
            "no_handling_days",
            "comment",
        ]
        help_texts = {
            "no_handling_days": "Сколько дней нельзя трогать",
        }


class CleaningEventForm(BaseEventForm):
    class Meta(BaseEventForm.Meta):
        fields = [
            "pet",
            "event_type",
            "event_datetime",
            "repeat_after_days",
            "comment",
        ]
        help_texts = {
            "repeat_after_days": "Через сколько дней нужна следующая уборка",
        }


class MeasurementEventForm(BaseEventForm):
    class Meta(BaseEventForm.Meta):
        fields = [
            "pet",
            "event_type",
            "event_datetime",
            "repeat_after_days",
            "weight_grams",
            "length_cm",
            "comment",
        ]
        help_texts = {
            "weight_grams": "Можно указать только вес или только длину",
            "length_cm": "Можно указать только длину или только вес",
        }


class CustomEventForm(BaseEventForm):
    class Meta(BaseEventForm.Meta):
        fields = [
            "pet",
            "event_type",
            "title",
            "event_datetime",
            "repeat_after_days",
            "no_handling_days",
            "comment",
        ]
        help_texts = {
            "repeat_after_days": "Если поле не нужно — можно оставить пустым.",
            "no_handling_days": "Если поле не нужно — можно оставить пустым.",
        }
