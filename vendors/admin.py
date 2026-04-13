from django.contrib import admin

from .models import Favorite, Media, Review, VendorProfile


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "category", "location")
    search_fields = ("user__username", "location", "category")


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor", "media_type", "file")
    list_filter = ("media_type",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("vendor", "customer", "rating", "created_at")
    list_filter = ("rating",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("customer", "vendor", "created_at")
