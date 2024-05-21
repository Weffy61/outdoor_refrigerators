from django.contrib.auth import logout
from django.shortcuts import render, redirect

from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CustomLoginForm, CustomUserCreationForm


class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'users/login.html'

    def get_success_url(self):
        return reverse_lazy('index')


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'users/registration.html'

    def get_success_url(self):
        return reverse_lazy('login')


def custom_logout_view(request):
    logout(request)
    return redirect('login')
