"""Tests for the `seed_demo` management command."""
import tempfile

from django.core.management import call_command
from django.test import TestCase, override_settings

from .models import Post
from users.models import User


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class SeedDemoCommandTests(TestCase):
    def test_creates_exactly_three_posts_and_the_demo_author(self):
        call_command('seed_demo')

        self.assertEqual(Post.objects.count(), 3)
        self.assertTrue(User.objects.filter(username='demo_author').exists())

    def test_seeded_posts_have_an_image_attached(self):
        call_command('seed_demo')

        for post in Post.objects.all():
            self.assertTrue(bool(post.image))

    def test_running_twice_does_not_duplicate_posts_or_the_author(self):
        call_command('seed_demo')
        call_command('seed_demo')

        self.assertEqual(Post.objects.count(), 3)
        self.assertEqual(User.objects.filter(username='demo_author').count(), 1)

    def test_demo_author_has_no_usable_password(self):
        call_command('seed_demo')

        author = User.objects.get(username='demo_author')
        self.assertFalse(author.has_usable_password())

    def test_seeded_posts_appear_on_the_home_page(self):
        call_command('seed_demo')

        # HomeView paginates 2 per page, so check both pages for all 3 posts.
        page_1 = self.client.get('/')
        page_2 = self.client.get('/', {'page': 2})
        combined = page_1.content + page_2.content

        for post in Post.objects.all():
            self.assertIn(post.title.encode(), combined)
