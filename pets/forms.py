from django import forms

from .models import Event, Pet


# ---------------- PET ----------------

class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = [
            "name",
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
            "status",
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
            "feeding_notes": "Чем кормить",
            "notes": "Заметки",
            "status": "Статус",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "animal_type": forms.Select(attrs={"class": "form-select"}),
            "species_name": forms.TextInput(attrs={"class": "form-control"}),
            "morph": forms.TextInput(attrs={"class": "form-control"}),
            "sex": forms.Select(attrs={"class": "form-select"}),
            "birth_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "acquired_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "weight_grams": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Например: 120"}),
            "length_cm": forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "feeding_notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Например: мыши, крысята, сверчки"
            }),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


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
                attrs={"type": "datetime-local", "class": "form-control"}
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
        super().__init__(*args, **kwargs)

        self.fields["event_datetime"].input_formats = ["%Y-%m-%dT%H:%M"]

        if user and not is_moderator:
            self.fields["pet"].queryset = Pet.objects.filter(owner=user)

        self.fields["event_type"].disabled = True


# ---------------- SPECIFIC FORMS ----------------

class FeedingEventForm(BaseEventForm):
    class Meta(BaseEventForm.Meta):
        fields = [
            "pet",
            "event_type",
            "event_datetime",
            "comment",
            "no_handling_days",
            "repeat_after_days",
        ]
        help_texts = {
            "no_handling_days": "Сколько дней нельзя брать животное после кормления",
            "repeat_after_days": "Когда нужно следующее кормление",
        }


class SheddingEventForm(BaseEventForm):
    class Meta(BaseEventForm.Meta):
        fields = [
            "pet",
            "event_type",
            "event_datetime",
            "comment",
            "no_handling_days",
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
            "comment",
            "repeat_after_days",
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
            "comment",
            "repeat_after_days",
            "no_handling_days",
            "weight_grams",
            "length_cm",
        ]