from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации пользователя."""

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "password1", "password2")
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "Введите email"}),
            "first_name": forms.TextInput(attrs={"placeholder": "Введите имя"}),
        }


class CustomAuthenticationForm(AuthenticationForm):
    """Форма авторизации пользователя по email."""

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True, "placeholder": "Введите email"}),
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Введите пароль"}),
    )


class CustomUserUpdateForm(forms.ModelForm):
    """Форма редактирования профиля пользователя."""

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "first_name",
            "last_name",
            "city",
            "phone_number",
            "avatar",
            "bio",
        )
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "Введите email"}),
            "first_name": forms.TextInput(attrs={"placeholder": "Введите имя"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Введите фамилию"}),
            "city": forms.TextInput(attrs={"placeholder": "Введите город"}),
            "phone_number": forms.TextInput(attrs={"placeholder": "Введите телефон"}),
            "bio": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Расскажите немного о себе"}
            ),
        }