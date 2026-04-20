from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

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
