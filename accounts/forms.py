"""
Registration and authentication-related forms.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class CustomAuthenticationForm(AuthenticationForm):
    """Login form with Bootstrap-friendly widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.setdefault("class", "form-control")
        self.fields["password"].widget.attrs.setdefault("class", "form-control")


class UserRegistrationForm(UserCreationForm):
    """Sign-up form with role selection (vendor or customer)."""

    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.RadioSelect,
        label="I am registering as",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "role", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        for name in ("username", "email", "password1", "password2"):
            self.fields[name].widget.attrs.setdefault("class", "form-control")
