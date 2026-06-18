"""
Forms for vendor profiles, media uploads, reviews, and customer search.
"""
from django import forms

from .choices import CATEGORY_CHOICES
from .models import Media, Review, VendorProfile


class MultipleFileInput(forms.FileInput):
    """HTML file input that allows multiple files (Django requires this flag)."""

    allow_multiple_selected = True


class VendorProfileForm(forms.ModelForm):
    """Vendor can edit display name via User, plus business fields."""

    full_name = forms.CharField(
        max_length=150,
        required=True,
        label="Full name",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES[1:],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = VendorProfile
        fields = ("phone", "category", "location", "description")
        widgets = {
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Phone for customers to call"}
            ),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Describe your services"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["full_name"].initial = self.user.get_full_name()

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            full = self.cleaned_data.get("full_name", "").strip()
            self.user.first_name = full[:150]
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile


class MediaUploadForm(forms.Form):
    """
    Upload multiple images and/or multiple videos in one submission.

    We use plain Field (not FileField): Django's FileField only validates a
    single file, but ``multiple`` on the input returns a list and breaks
    FileField validation. The view saves using request.FILES.getlist(...).
    """

    images = forms.Field(
        required=False,
        widget=MultipleFileInput(
            attrs={
                "class": "form-control",
                "multiple": True,
                "accept": "image/*",
            }
        ),
    )
    videos = forms.Field(
        required=False,
        widget=MultipleFileInput(
            attrs={
                "class": "form-control",
                "multiple": True,
                "accept": "video/*",
            }
        ),
    )

    def clean(self):
        super().clean()
        imgs = self.files.getlist("images")
        vids = self.files.getlist("videos")
        if not imgs and not vids:
            raise forms.ValidationError("Select at least one image or video to upload.")


class VendorSearchForm(forms.Form):
    """Customer search filters (category and location)."""

    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=False,
        initial="",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "City or area"}),
    )


class ReviewForm(forms.ModelForm):
    """Simple star review with optional comment."""

    class Meta:
        model = Review
        fields = ("rating", "text")
        widgets = {
            "rating": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "max": 5, "step": 1}
            ),
            "text": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
