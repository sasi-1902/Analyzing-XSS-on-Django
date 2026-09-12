"""
python manage.py seed_demo

Idempotently creates the demo author and exactly three neutral blog posts,
using the source images already checked into static/blog/. Safe to run
more than once: existing posts (matched by slug) and the existing author
(matched by username) are left untouched.
"""
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from core.models import Post
from users.models import User

DEMO_AUTHOR_USERNAME = 'demo_author'
DEMO_AUTHOR_EMAIL = 'demo-author@example.com'

# Order matters: xss_lab's Stored XSS demonstration reads comments on the
# first post below (see xss_lab/views.py:DEMO_POST_SLUG).
DEMO_POSTS = [
    {
        'title': 'Mobile Commerce and Everyday Shopping',
        'image': 'ecommerce.png',
        'content': (
            "Mobile devices have changed how people shop for everyday items. A quick "
            "search, a saved card, and a few taps are often enough to compare prices "
            "and complete a purchase without visiting a store.\n\n"
            "Notifications, saved carts, and one-tap checkout mean a process that once "
            "took a special trip now fits into a short break."
        ),
    },
    {
        'title': 'Connected Devices in Daily Life',
        'image': 'connected-devices.png',
        'content': (
            "Phones, watches, speakers, and home sensors increasingly talk to each "
            "other. A single app can adjust lighting, check a delivery, or start a "
            "playlist without much thought.\n\n"
            "None of this is dramatic on its own, but together it adds up to a home "
            "that responds a little more to what people are doing."
        ),
    },
    {
        'title': 'A Short Travel Note from Honolulu',
        'image': 'travel.png',
        'content': (
            "A short stop in Honolulu was long enough for an early walk along the "
            "shore before the day got busy. The air was warm even before sunrise, "
            "and the beach was mostly quiet.\n\n"
            "Sometimes the best part of a trip is a single unhurried morning rather "
            "than a full itinerary."
        ),
    },
]


class Command(BaseCommand):
    help = (
        'Idempotently seed the blog with the demo author and exactly three '
        'neutral demo posts, using the images already under static/blog/.'
    )

    def handle(self, *args, **options):
        author, created = User.objects.get_or_create(
            username=DEMO_AUTHOR_USERNAME,
            defaults={'email': DEMO_AUTHOR_EMAIL},
        )
        if created:
            author.set_unusable_password()
            author.save()
            self.stdout.write(self.style.SUCCESS(f'Created demo author "{author.username}".'))
        else:
            self.stdout.write(f'Demo author "{author.username}" already exists.')

        for entry in DEMO_POSTS:
            slug = slugify(entry['title'])

            if Post.objects.filter(slug=slug).exists():
                self.stdout.write(f'Post "{entry["title"]}" already exists, skipping.')
                continue

            post = Post(
                title=entry['title'],
                slug=slug,
                author=author,
                content=entry['content'],
            )

            source_image = settings.BASE_DIR / 'static' / 'blog' / entry['image']
            with source_image.open('rb') as image_file:
                # Copies the file into MEDIA_ROOT via Django's storage API
                # (not a raw filesystem copy) -- this is what makes the
                # resulting media file/runtime data, not project source.
                post.image.save(entry['image'], File(image_file), save=False)

            post.save()
            self.stdout.write(self.style.SUCCESS(f'Created post "{entry["title"]}".'))
