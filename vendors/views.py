"""
Views for home, vendor dashboard, customer dashboard, public vendor profile, and extras.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import MediaUploadForm, ReviewForm, VendorProfileForm, VendorSearchForm
from .models import Favorite, Media, Review, VendorProfile


def home(request):
    """Landing page with platform description, login/register, and static demo cards only."""
    return render(request, "home.html")


def _vendor_queryset():
    """Vendors with related user; media prefetched where useful."""
    return VendorProfile.objects.select_related("user").order_by("user__username")


@login_required
@require_http_methods(["GET", "POST"])
def vendor_dashboard(request):
    """Vendor-only: edit profile, upload/delete media."""
    if not request.user.is_vendor:
        messages.warning(request, "That area is for vendors.")
        return redirect("vendors:customer_dashboard")

    profile = get_object_or_404(VendorProfile, user=request.user)
    profile_form = VendorProfileForm(
        instance=profile,
        user=request.user,
        prefix="profile",
    )
    media_form = MediaUploadForm()

    if request.method == "POST":
        if "save_profile" in request.POST:
            profile_form = VendorProfileForm(
                request.POST,
                instance=profile,
                user=request.user,
                prefix="profile",
            )
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated.")
                return redirect("vendors:vendor_dashboard")
        elif "upload_media" in request.POST:
            media_form = MediaUploadForm(request.POST, request.FILES)
            if media_form.is_valid():
                created = 0
                for f in request.FILES.getlist("images"):
                    if f and getattr(f, "name", None):
                        Media.objects.create(
                            vendor=profile,
                            file=f,
                            media_type=Media.TYPE_IMAGE,
                        )
                        created += 1
                for f in request.FILES.getlist("videos"):
                    if f and getattr(f, "name", None):
                        Media.objects.create(
                            vendor=profile,
                            file=f,
                            media_type=Media.TYPE_VIDEO,
                        )
                        created += 1
                messages.success(request, f"Uploaded {created} file(s).")
                return redirect("vendors:vendor_dashboard")
            else:
                messages.error(request, "Please fix the upload errors below.")

    media_list = profile.media_files.all()
    return render(
        request,
        "vendors/vendor_dashboard.html",
        {
            "profile": profile,
            "profile_form": profile_form,
            "media_form": media_form,
            "media_list": media_list,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def customer_dashboard(request):
    """Customer-only: search vendors by category and location; card list."""
    if not request.user.is_customer:
        messages.warning(request, "That area is for customers.")
        return redirect("vendors:vendor_dashboard")

    form = VendorSearchForm(request.GET)
    vendors = _vendor_queryset()

    if form.is_valid():
        cat = form.cleaned_data.get("category") or ""
        loc = (form.cleaned_data.get("location") or "").strip()
        if cat:
            vendors = vendors.filter(category=cat)
        if loc:
            vendors = vendors.filter(location__icontains=loc)

    # Attach first image for cards (avoid N+1 queries).
    vendor_rows = []
    for v in vendors:
        fi = v.first_image()
        vendor_rows.append({"vendor": v, "thumb": fi})

    return render(
        request,
        "vendors/customer_dashboard.html",
        {
            "search_form": form,
            "vendor_rows": vendor_rows,
        },
    )


def vendor_profile(request, pk):
    """Public vendor detail: galleries, reviews, call link, favorite/review for customers."""
    vendor = get_object_or_404(
        VendorProfile.objects.select_related("user"),
        pk=pk,
    )
    images = vendor.media_files.filter(media_type=Media.TYPE_IMAGE)
    videos = vendor.media_files.filter(media_type=Media.TYPE_VIDEO)
    reviews = vendor.reviews.select_related("customer").order_by("-created_at")
    avg = vendor.average_rating()
    count = vendor.review_count()

    is_favorite = False
    if request.user.is_authenticated and request.user.is_customer:
        is_favorite = Favorite.objects.filter(customer=request.user, vendor=vendor).exists()

    review_form = None
    can_review = False
    if request.user.is_authenticated and request.user.is_customer:
        can_review = not Review.objects.filter(vendor=vendor, customer=request.user).exists()

    if request.method == "POST" and "submit_review" in request.POST:
        if not request.user.is_authenticated or not request.user.is_customer:
            raise PermissionDenied
        if not can_review:
            messages.error(request, "You have already reviewed this vendor.")
            return redirect(vendor.get_absolute_url())
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            rev = review_form.save(commit=False)
            rev.vendor = vendor
            rev.customer = request.user
            rev.save()
            messages.success(request, "Thank you for your review.")
            return redirect(vendor.get_absolute_url())
    elif can_review:
        review_form = ReviewForm()

    return render(
        request,
        "vendors/vendor_profile.html",
        {
            "vendor": vendor,
            "images": images,
            "videos": videos,
            "reviews": reviews,
            "avg_rating": avg,
            "review_count": count,
            "is_favorite": is_favorite,
            "review_form": review_form,
            "can_review": can_review,
        },
    )


@login_required
@require_POST
def delete_media(request, pk):
    """Delete one media file (owner vendor only)."""
    media = get_object_or_404(Media, pk=pk)
    if not request.user.is_vendor or media.vendor.user_id != request.user.id:
        raise PermissionDenied
    media.delete()
    messages.success(request, "Media removed.")
    return redirect("vendors:vendor_dashboard")


@login_required
@require_POST
def toggle_favorite(request, pk):
    """Customer toggles favorite vendor."""
    vendor = get_object_or_404(VendorProfile, pk=pk)
    if not request.user.is_customer:
        raise PermissionDenied
    fav, created = Favorite.objects.get_or_create(customer=request.user, vendor=vendor)
    if not created:
        fav.delete()
        messages.info(request, "Removed from favorites.")
    else:
        messages.success(request, "Added to favorites.")
    next_url = request.POST.get("next") or vendor.get_absolute_url()
    return redirect(next_url)


@login_required
@require_http_methods(["GET"])
def favorites_list(request):
    """List customer's favorite vendors."""
    if not request.user.is_customer:
        messages.warning(request, "Favorites are for customers.")
        return redirect("vendors:vendor_dashboard")
    favs = Favorite.objects.filter(customer=request.user).select_related(
        "vendor", "vendor__user"
    )
    vendor_rows = []
    for f in favs:
        v = f.vendor
        vendor_rows.append({"vendor": v, "thumb": v.first_image()})
    return render(
        request,
        "vendors/favorites.html",
        {"vendor_rows": vendor_rows},
    )
