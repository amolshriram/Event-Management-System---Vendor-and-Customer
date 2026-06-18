"""Shared category choices for vendor profiles and search."""

CATEGORY_CHOICES = [
    ("", "— Any category —"),
    ("photographer", "Photographer"),
    ("caterer", "Caterer"),
    ("decorator", "Decorator"),
    ("musician", "Musician / DJ"),
    ("venue", "Venue"),
    ("planner", "Event Planner"),
    ("other", "Other"),
]

# Slug -> human-readable label (excludes the empty "any" option).
CATEGORY_LABELS = dict(CATEGORY_CHOICES[1:])
