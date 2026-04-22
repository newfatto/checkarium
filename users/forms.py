from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from users.constants import TIME_ZONE_CHOICES

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации пользователя."""

    time_zone = forms.ChoiceField(
        choices=TIME_ZONE_CHOICES,
        label="Часовой пояс",
        widget=forms.Select(attrs={"class": "form-control-ui"}),
        help_text="Выберите ваш часовой пояс. Например: UTC+3 для Москвы.",
    )

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "time_zone", "password1", "password2")
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Введите email",
                    "class": "form-control-ui",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "placeholder": "Введите имя",
                    "class": "form-control-ui",
                }
            ),
        }

    def __init__(self, *args, **kwargs) -> None:
        """Настроить отображение полей формы."""
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {
                "placeholder": "Введите пароль",
                "class": "form-control-ui",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "placeholder": "Повторите пароль",
                "class": "form-control-ui",
            }
        )

    def clean_email(self) -> str:
        """Проверяет уникальность email без учёта регистра."""
        email = self.cleaned_data["email"].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email

    def clean_first_name(self) -> str:
        """Убирает лишние пробелы в имени."""
        return self.cleaned_data["first_name"].strip()


class CustomAuthenticationForm(AuthenticationForm):
    """Форма авторизации пользователя по email."""

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "autofocus": True,
                "placeholder": "Введите email",
                "class": "form-control-ui",
            }
        ),
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Введите пароль",
                "class": "form-control-ui",
            }
        ),
    )


class CustomUserUpdateForm(forms.ModelForm):
    """Форма редактирования профиля пользователя."""

    time_zone = forms.ChoiceField(
        choices=TIME_ZONE_CHOICES,
        label="Часовой пояс",
        widget=forms.Select(attrs={"class": "form-control-ui"}),
        help_text="Например: UTC+3 для Москвы, UTC+2 для Нидерландов зимой.",
    )

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "first_name",
            "last_name",
            "city",
            "phone_number",
            "time_zone",
            "avatar",
            "bio",
        )
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Введите email",
                    "class": "form-control-ui",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "placeholder": "Введите имя",
                    "class": "form-control-ui",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "placeholder": "Введите фамилию",
                    "class": "form-control-ui",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "placeholder": "Введите город",
                    "class": "form-control-ui",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "placeholder": "Введите телефон",
                    "class": "form-control-ui",
                }
            ),
            "bio": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Расскажите немного о себе",
                    "class": "form-textarea-ui",
                }
            ),
        }

    def __init__(self, *args, **kwargs) -> None:
        """Настроить отображение полей формы."""
        super().__init__(*args, **kwargs)
        self.fields["avatar"].widget.attrs.update({"class": "form-control-ui"})

    def clean_email(self) -> str:
        """Проверяет уникальность email без учёта регистра."""
        email = self.cleaned_data["email"].strip().lower()
        qs = CustomUser.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email

    def clean_first_name(self) -> str:
        """Убирает лишние пробелы в имени."""
        return self.cleaned_data["first_name"].strip()

    def clean_last_name(self) -> str:
        """Убирает лишние пробелы в фамилии."""
        return self.cleaned_data.get("last_name", "").strip()

    def clean_phone_number(self) -> str:
        """Убирает лишние пробелы в телефоне."""
        return self.cleaned_data.get("phone_number", "").strip()
