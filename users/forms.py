from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from users.models import CustomUser


class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Email'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Пароль'
        })
        self.fields['remember_me'] = forms.BooleanField(
            required=False,
            widget=forms.CheckboxInput(attrs={
                'class': 'checkbox'
            })
        )


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['email'].widget.attrs.update({
            'autofocus': True,
            'type': 'email',
            'class': 'form-control',
            'placeholder': 'Email'
        })

        self.fields['first_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Имя',
            'required': True
        })

        self.fields['last_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Фамилия',
            'required': True

        })

        self.fields['password1'].widget.attrs.update({
            'type': 'password',
            'class': 'form-control',
            'placeholder': 'Пароль'
        })

        self.fields['password2'].widget.attrs.update({
            'type': 'password',
            'class': 'form-control',
            'placeholder': 'Подтверждение пароля'
        })
