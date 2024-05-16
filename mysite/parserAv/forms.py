from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError


class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'placeholder': 'Логин'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'}))
    password2 = forms.CharField(label='Подтвердите пароль', widget=forms.PasswordInput(
        attrs={'placeholder': 'Подтвердите пароль'}))

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2',)

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError('Аккаунт с такой почтой уже существует.')
        return email

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if CustomUser.objects.filter(email__iexact=username).exists():
            raise ValidationError('Аккаунт с такой почтой уже существует.')
        return username


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'placeholder': 'Логин'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'}))
