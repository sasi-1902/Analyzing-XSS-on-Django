from django.urls import reverse
from django.test import TestCase
from django.utils.text import slugify

from .models import Post
from users.models import User


class PostCreateViewTest(TestCase):
    def test_post_create_stores_user(self):
        user1 = User.objects.create_user(
            username='user1', email='user1@gmail.com', password='1234'
        )
        post_data = {
            'title': 'test post',
            'content': 'Hello world',
        }
        self.client.force_login(user1)
        self.client.post(reverse('core:post_create'), post_data)

        self.assertTrue(Post.objects.filter(author=user1).exists())


class PostUpdateViewTest(TestCase):
    def test_post_update_returns_404(self):
        user1 = User.objects.create_user(
            username='user1', email='user1@gmail.com', password='1234'
        )
        user2 = User.objects.create_user(
            username='user2', email='user2@gmail.com', password='1234'
        )
        post = Post.objects.create(
            author=user1, title='test post', content='Hello world')

        self.client.force_login(user2)
        response = self.client.post(
            reverse('core:post_update', kwargs=({'pk': post.id})),
            {'title': 'change title'}
        )
        self.assertEqual(response.status_code, 404)


class HomeViewPaginationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user1', email='user1@gmail.com', password='1234'
        )
        # HomeView paginates 2 per page -- 3 posts guarantees a second page.
        for i in range(3):
            title = f'post {i}'
            Post.objects.create(
                author=self.user, title=title, slug=slugify(title), content='hello',
            )

    def test_home_page_renders_valid_pagination_markup(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        # Regression: the "Previous" link on page 1 used to render as
        # `href="#""` (an extra stray quote).
        self.assertNotContains(response, 'href="#""')

    def test_second_page_is_reachable(self):
        response = self.client.get(reverse('core:home'), {'page': 2})
        self.assertEqual(response.status_code, 200)

    def test_home_page_shows_author_username_not_email(self):
        # Regression: {{ post.author }} used to render the User model's
        # default __str__, which is the email (USERNAME_FIELD='email').
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, self.user.username)
        self.assertNotContains(response, self.user.email)


class PostDetailAuthorTest(TestCase):
    def test_post_detail_shows_author_username_not_email(self):
        user = User.objects.create_user(
            username='user1', email='user1@gmail.com', password='1234'
        )
        post = Post.objects.create(
            author=user, title='hello world', slug='hello-world', content='hi',
        )
        response = self.client.get(reverse('core:post', args=[post.id, post.slug]))
        self.assertContains(response, user.username)
        self.assertNotContains(response, user.email)


class SearchViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user1', email='user1@gmail.com', password='1234'
        )
        self.post = Post.objects.create(
            author=self.user, title='hello world', slug='hello-world', content='hi',
        )

    def test_search_lives_under_blog_search(self):
        response = self.client.get(reverse('core:search'), {'q': 'hello'})
        self.assertEqual(response.status_code, 200)

    def test_search_result_link_resolves_to_the_post(self):
        response = self.client.get(reverse('core:search'), {'q': 'hello'})
        expected_url = reverse('core:post', args=[self.post.id, self.post.slug])
        self.assertContains(response, f'href="{expected_url}"')

    def test_search_lives_at_the_site_root_search_path(self):
        # The blog is the primary application, so search lives directly
        # at /search/ -- no redirect shim is needed or exists.
        self.assertEqual(reverse('core:search'), '/search/')
