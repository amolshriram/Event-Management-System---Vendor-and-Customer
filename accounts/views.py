"""
Authentication views: registration, login, logout, and role-based dashboard redirect.
"""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from vendors.models import VendorProfile

from .forms import CustomAuthenticationForm, UserRegistrationForm


@ensure_csrf_cookie
def register_view(request):
    """Create a new user; vendors get an empty VendorProfile for the dashboard."""
    if request.user.is_authenticated:
        messages.info(
            request,
            "You are already signed in. Log out first if you need to create another account.",
        )
        return redirect("dashboard_redirect")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = form.cleaned_data["role"]
            user.save()
            if user.role == user.ROLE_VENDOR:
                VendorProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, "Welcome! Your account has been created.")
            return redirect("dashboard_redirect")
    else:
        form = UserRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        # Explain why login page is skipped when a session already exists.
        if self.redirect_authenticated_user and request.user.is_authenticated:
            messages.info(
                request,
                "You are already signed in. Log out first to log in with a different account.",
            )
            return HttpResponseRedirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        # Honor ?next= / POST next= when safe; otherwise route by role.
        redirect_to = self.get_redirect_url()
        if redirect_to:
            return redirect_to
        return reverse("dashboard_redirect")


class CustomLogoutView(LogoutView):
    # Home lives in the vendors app URLconf (namespace vendors).
    next_page = reverse_lazy("vendors:home")


def dashboard_redirect(request):
    """Send the user to the correct dashboard based on role."""
    if not request.user.is_authenticated:
        return redirect("login")

    if request.user.is_vendor:
        return redirect("vendors:vendor_dashboard")
    return redirect("vendors:customer_dashboard")
