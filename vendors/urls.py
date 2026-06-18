from django.urls import path

from . import views

app_name = "vendors"

urlpatterns = [
    path("", views.home, name="home"),
    path("vendor/dashboard/", views.vendor_dashboard, name="vendor_dashboard"),
    path("customer/dashboard/", views.customer_dashboard, name="customer_dashboard"),
    path("customer/favorites/", views.favorites_list, name="favorites"),
    path("vendor/<int:pk>/", views.vendor_profile, name="vendor_profile"),
    path("media/<int:pk>/delete/", views.delete_media, name="delete_media"),
    path("vendor/<int:pk>/favorite/", views.toggle_favorite, name="toggle_favorite"),
]
