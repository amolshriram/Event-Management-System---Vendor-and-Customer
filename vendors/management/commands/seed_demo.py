"""
Load demo vendor profiles (and optional demo customer) for local development / UI previews.

Usage:
    python manage.py seed_demo

All demo accounts use password: demo12345
"""

from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from vendors.models import Media, Review, VendorProfile

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None


DEMO_PASSWORD = "demo12345"

DEMO_VENDORS = [
    {
        "username": "demo_photographer",
        "email": "photographer@demo.local",
        "full_name": "Lens & Light Photography",
        "phone": "+91-90000-10001",
        "category": "photographer",
        "location": "Mumbai",
        "description": "Wedding and event photography with candid and traditional coverage. "
        "Drone shots available on request.",
        "accent": (41, 98, 255),
        "label": "Photo",
    },
    {
        "username": "demo_caterer",
        "email": "caterer@demo.local",
        "full_name": "Spice Route Catering",
        "phone": "+91-90000-10002",
        "category": "caterer",
        "location": "Pune",
        "description": "North Indian, South Indian, and live counters for weddings and corporate events.",
        "accent": (220, 53, 69),
        "label": "Cater",
    },
    {
        "username": "demo_decorator",
        "email": "decorator@demo.local",
        "full_name": "Bloom & Ribbon Events",
        "phone": "+91-90000-10003",
        "category": "decorator",
        "location": "Bengaluru",
        "description": "Stage décor, floral arrangements, lighting, and theme-based setups for all occasions.",
        "accent": (25, 135, 84),
        "label": "Decor",
    },
]


def _make_placeholder_png(width: int, height: int, rgb: tuple, text: str) -> bytes:
    """Build a simple labeled PNG in memory."""
    if Image is None:
        return (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
            b"\x01\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
    img = Image.new("RGB", (width, height), rgb)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = max(8, (width - tw) // 2)
    y = max(8, (height - th) // 2)
    draw.text((x, y), text, fill=(255, 255, 255), font=font)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class Command(BaseCommand):
    help = "Create demo vendor profiles with sample images (password for all: demo12345)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo_* users and recreate (destructive).",
        )

    def handle(self, *args, **options):
        reset = options["reset"]
        if reset:
            User.objects.filter(username__startswith="demo_").delete()
            self.stdout.write(self.style.WARNING("Removed existing demo_* users."))

        with transaction.atomic():
            for spec in DEMO_VENDORS:
                self._ensure_vendor(spec)

            self._ensure_demo_customer_reviews()

        self.stdout.write(self.style.SUCCESS("Demo data ready. Password for all demo accounts: demo12345"))

    def _ensure_vendor(self, spec):
        user, created = User.objects.get_or_create(
            username=spec["username"],
            defaults={
                "email": spec["email"],
                "role": User.ROLE_VENDOR,
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        user.first_name = spec["full_name"][:150]
        user.email = spec["email"]
        user.role = User.ROLE_VENDOR
        user.save()

        profile, _ = VendorProfile.objects.update_or_create(
            user=user,
            defaults={
                "phone": spec["phone"],
                "category": spec["category"],
                "location": spec["location"],
                "description": spec["description"],
            },
        )

        if profile.media_files.filter(media_type=Media.TYPE_IMAGE).exists():
            return

        for i, label in enumerate([spec["label"] + " sample 1", spec["label"] + " sample 2"]):
            png = _make_placeholder_png(
                520,
                320,
                spec["accent"],
                label,
            )
            name = f"{spec['username']}_sample_{i + 1}.png"
            m = Media(
                vendor=profile,
                media_type=Media.TYPE_IMAGE,
            )
            m.file.save(name, ContentFile(png), save=True)

    def _ensure_demo_customer_reviews(self):
        """Optional demo customer + short reviews for average ratings."""
        cust, created = User.objects.get_or_create(
            username="demo_customer",
            defaults={
                "email": "customer@demo.local",
                "role": User.ROLE_CUSTOMER,
            },
        )
        if created:
            cust.set_password(DEMO_PASSWORD)
            cust.save()

        snippets = [
            ("demo_photographer", 5, "Beautiful shots of our reception!"),
            ("demo_caterer", 5, "Guests loved the food."),
            ("demo_decorator", 4, "Stunning stage setup."),
        ]
        for uname, stars, text in snippets:
            try:
                vendor_user = User.objects.get(username=uname)
                profile = vendor_user.vendor_profile
            except (User.DoesNotExist, VendorProfile.DoesNotExist):
                continue
            Review.objects.get_or_create(
                vendor=profile,
                customer=cust,
                defaults={"rating": stars, "text": text},
            )
