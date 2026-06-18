"""
Vendor profiles, media uploads, reviews, and favorites for the Event Vendor Platform.
"""
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.urls import reverse

from .choices import CATEGORY_LABELS


class VendorProfile(models.Model):
    """Extended profile for users who register as vendors."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vendor_profile",
    )
    phone = models.CharField(max_length=20, blank=True, default="")
    category = models.CharField(max_length=100, blank=True, default="")
    location = models.CharField(max_length=200, blank=True, default="")
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return f"Vendor: {self.user.get_full_name() or self.user.username}"

    def get_absolute_url(self):
        return reverse("vendors:vendor_profile", kwargs={"pk": self.pk})

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username

    def category_label(self):
        """Human-readable category for templates."""
        return CATEGORY_LABELS.get(self.category, self.category or "—")

    def first_image(self):
        """First uploaded image (used as card thumbnail on customer dashboard)."""
        return self.media_files.filter(media_type=Media.TYPE_IMAGE).order_by("id").first()

    def average_rating(self):
        """Average star rating from reviews (None if no reviews)."""
        agg = self.reviews.aggregate(avg=Avg("rating"))
        return agg["avg"]

    def review_count(self):
        return self.reviews.count()


class Media(models.Model):
    """Image or video file belonging to a vendor."""

    TYPE_IMAGE = "image"
    TYPE_VIDEO = "video"
    MEDIA_TYPE_CHOICES = [
        (TYPE_IMAGE, "Image"),
        (TYPE_VIDEO, "Video"),
    ]

    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name="media_files",
    )
    file = models.FileField(upload_to="vendor_media/%Y/%m/")
    # Stores whether this upload is image or video (spec: type image/video).
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)

    class Meta:
        ordering = ["id"]
        verbose_name_plural = "Media"

    def __str__(self):
        return f"{self.get_media_type_display()} for {self.vendor_id}"


class Review(models.Model):
    """Customer review with star rating and optional text."""

    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vendor_reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    text = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        # One review per customer per vendor (simple rule)
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "customer"],
                name="unique_review_per_customer_vendor",
            )
        ]

    def __str__(self):
        return f"Review {self.rating}★ by {self.customer} on {self.vendor_id}"


class Favorite(models.Model):
    """Customer bookmark for a vendor profile."""

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_vendors",
    )
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "vendor"],
                name="unique_favorite_per_customer_vendor",
            )
        ]

    def __str__(self):
        return f"{self.customer} ♥ {self.vendor_id}"
