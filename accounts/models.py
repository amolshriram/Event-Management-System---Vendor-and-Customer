"""
Custom user model extending Django's AbstractUser with a role field
(vendor or customer) for the Event Vendor Platform.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Application user with role-based access (vendor vs customer)."""

    ROLE_VENDOR = "vendor"
    ROLE_CUSTOMER = "customer"
    ROLE_CHOICES = [
        (ROLE_VENDOR, "Vendor"),
        (ROLE_CUSTOMER, "Customer"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_CUSTOMER,
        db_index=True,
    )

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_vendor(self):
        return self.role == self.ROLE_VENDOR

    @property
    def is_customer(self):
        return self.role == self.ROLE_CUSTOMER
