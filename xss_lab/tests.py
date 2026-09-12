"""
Regression tests for the XSS security layer.

These confirm the vulnerable pages stay reproducibly vulnerable (so they
keep demonstrating what they claim to) and that every secure counterpart
actually escapes the same payload -- using the blog's real Post/Comment
data and search, not a parallel demonstration-only model. All payloads
are harmless and local only -- nothing here contacts an external service.
"""
import tempfile

from django.conf import settings
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.models import Comment, Post
from core.xss_audit_rules import scan_path

from .views import DEMO_POST_SLUG

PAYLOAD = '<script>alert(1)</script>'
ESCAPED_PAYLOAD = '&lt;script&gt;alert(1)&lt;/script&gt;'

DOM_PAYLOAD = '<img src=x onerror=alert(1)>'


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class StoredXssTests(TestCase):
    """
    Stored XSS is demonstrated on a real blog post's real comments
    (core.models.Comment), seeded by `seed_demo`. MEDIA_ROOT is
    overridden so seeding the demo post's image during tests never
    writes into the project's real media/ directory.
    """

    def setUp(self):
        call_command('seed_demo')
        self.post = Post.objects.get(slug=DEMO_POST_SLUG)

    def _post_comment(self, client, url_name):
        return client.post(reverse(f'xss_lab:{url_name}'), {
            'name': PAYLOAD,
            'email': 'demo@example.com',
            'content': 'hello',
        }, follow=True)

    def test_vulnerable_page_renders_raw_payload(self):
        response = self._post_comment(self.client, 'stored_vulnerable')
        self.assertContains(response, PAYLOAD, html=False)

    def test_secure_page_escapes_the_same_stored_comment(self):
        self._post_comment(self.client, 'stored_vulnerable')
        response = self.client.get(reverse('xss_lab:stored_secure'))
        self.assertContains(response, ESCAPED_PAYLOAD, html=False)
        self.assertNotContains(response, PAYLOAD, html=False)

    def test_comment_is_a_real_comment_on_the_real_post(self):
        self._post_comment(self.client, 'stored_vulnerable')
        comment = Comment.objects.get(name=PAYLOAD)
        self.assertEqual(comment.post_id, self.post.id)

    def test_payload_persists_across_separate_client_sessions(self):
        posting_client = Client()
        other_client = Client()

        self._post_comment(posting_client, 'stored_vulnerable')

        response = other_client.get(reverse('xss_lab:stored_vulnerable'))
        self.assertContains(response, PAYLOAD, html=False)

    def test_both_pages_show_the_real_post_content(self):
        response = self.client.get(reverse('xss_lab:stored_vulnerable'))
        self.assertContains(response, self.post.title)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ReflectedXssTests(TestCase):
    def setUp(self):
        call_command('seed_demo')

    def test_vulnerable_page_returns_raw_payload(self):
        response = self.client.get(reverse('xss_lab:reflected_vulnerable'), {'q': PAYLOAD})
        self.assertContains(response, f'You searched for: {PAYLOAD}', html=False)

    def test_secure_page_escapes_payload(self):
        response = self.client.get(reverse('xss_lab:reflected_secure'), {'q': PAYLOAD})
        self.assertContains(response, f'You searched for: {ESCAPED_PAYLOAD}', html=False)
        self.assertNotContains(response, f'You searched for: {PAYLOAD}', html=False)

    def test_uses_the_real_blog_search_results(self):
        post = Post.objects.first()
        response = self.client.get(reverse('xss_lab:reflected_vulnerable'), {'q': post.title[:6]})
        self.assertContains(response, post.title)


class DomXssTests(TestCase):
    def test_vulnerable_page_contains_unsafe_sink(self):
        response = self.client.get(reverse('xss_lab:dom_vulnerable'))
        self.assertContains(response, 'result.innerHTML = input.value', html=False)

    def test_secure_page_uses_safe_sink(self):
        response = self.client.get(reverse('xss_lab:dom_secure'))
        self.assertContains(response, 'result.textContent = input.value', html=False)
        self.assertNotContains(response, 'result.innerHTML = input.value', html=False)

    def test_pages_recommend_event_handler_payload_not_script_tag(self):
        # A <script> tag is not a useful DOM XSS demo: browsers do not
        # execute <script> elements inserted via innerHTML.
        for name in ('dom_vulnerable', 'dom_secure'):
            response = self.client.get(reverse(f'xss_lab:{name}'))
            self.assertContains(response, 'onerror=alert(1)', html=False)
            self.assertNotContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;', html=False)


class IndexPageTests(TestCase):
    def test_index_returns_200_and_lists_all_four_items(self):
        response = self.client.get(reverse('xss_lab:index'))
        self.assertEqual(response.status_code, 200)
        for text in ('Stored XSS', 'Reflected XSS', 'DOM-based XSS', 'XSS Auditor'):
            self.assertContains(response, text)

    def test_index_links_to_every_demonstration_and_the_auditor(self):
        response = self.client.get(reverse('xss_lab:index'))
        for name in (
            'stored_vulnerable', 'stored_secure',
            'reflected_vulnerable', 'reflected_secure',
            'dom_vulnerable', 'dom_secure',
            'auditor',
        ):
            self.assertContains(response, reverse(f'xss_lab:{name}'))

    def test_index_prompts_to_seed_when_no_demo_post_exists(self):
        response = self.client.get(reverse('xss_lab:index'))
        self.assertContains(response, 'python manage.py seed_demo')

    def test_index_does_not_use_exercise_terminology(self):
        response = self.client.get(reverse('xss_lab:index'))
        content = response.content.decode()
        for banned in ('ATTACK', 'OBSERVE', 'VERIFY', 'exercise', 'guided'):
            self.assertNotIn(banned, content)


class GuidePageTests(TestCase):
    def test_guide_page_returns_200(self):
        response = self.client.get(reverse('xss_lab:guide'))
        self.assertEqual(response.status_code, 200)

    def test_guide_walks_through_the_running_site_not_setup(self):
        response = self.client.get(reverse('xss_lab:guide'))
        # This is a user guide to the running site, not repository setup --
        # that belongs in README.md instead.
        for setup_text in (
            'python -m venv', 'pip install', 'python manage.py migrate',
            'python manage.py seed_demo', 'python manage.py test',
        ):
            self.assertNotContains(response, setup_text)

    def test_guide_covers_all_seven_steps(self):
        response = self.client.get(reverse('xss_lab:guide'))
        for step in (
            'Explore the Blog', 'Open the XSS Lab', 'Stored XSS',
            'Reflected XSS', 'DOM XSS', 'Auditor', 'Finish',
        ):
            self.assertContains(response, step)

    def test_guide_links_to_every_page_it_walks_through(self):
        response = self.client.get(reverse('xss_lab:guide'))
        for name in (
            'stored_vulnerable', 'stored_secure',
            'reflected_vulnerable', 'reflected_secure',
            'dom_vulnerable', 'dom_secure',
            'auditor', 'index',
        ):
            self.assertContains(response, reverse(f'xss_lab:{name}'))
        self.assertContains(response, reverse('core:home'))

    def test_guide_explains_auditor_columns(self):
        response = self.client.get(reverse('xss_lab:guide'))
        for word in ('rule', 'severity', 'file and line', 'snippet'):
            self.assertContains(response, word)

    def test_guide_does_not_use_exercise_terminology(self):
        response = self.client.get(reverse('xss_lab:guide'))
        content = response.content.decode()
        for banned in ('ATTACK', 'OBSERVE', 'RESET LAB'):
            self.assertNotIn(banned, content)


class AuditorPageTests(TestCase):
    def test_auditor_page_returns_200(self):
        response = self.client.get(reverse('xss_lab:auditor'))
        self.assertEqual(response.status_code, 200)

    def test_auditor_page_shows_human_review_disclaimer(self):
        response = self.client.get(reverse('xss_lab:auditor'))
        self.assertContains(
            response,
            'Static heuristic analysis &mdash; findings require human review.',
            html=False,
        )

    def test_auditor_page_lists_a_known_vulnerable_finding(self):
        response = self.client.get(reverse('xss_lab:auditor'))
        self.assertContains(response, 'DJX001')
        self.assertContains(response, 'stored_vulnerable.html')

    def test_auditor_page_does_not_accept_a_path_input(self):
        response = self.client.get(reverse('xss_lab:auditor'))
        self.assertNotContains(response, 'name="path"')

    def test_auditor_page_ignores_a_submitted_path_parameter(self):
        response = self.client.get(reverse('xss_lab:auditor'), {'path': '/etc'})
        self.assertContains(response, 'DJX001')

    def test_auditor_excludes_scanner_implementation_and_tests(self):
        response = self.client.get(reverse('xss_lab:auditor'))
        self.assertNotContains(response, 'xss_audit_rules.py')
        self.assertNotContains(response, 'test_xss_audit.py')

    def test_auditor_page_does_not_expose_the_absolute_base_dir(self):
        response = self.client.get(reverse('xss_lab:auditor'))
        self.assertNotContains(response, str(settings.BASE_DIR))
        self.assertNotContains(response, str(settings.BASE_DIR.parent))

    def test_auditor_page_shows_a_neutral_project_root_label(self):
        response = self.client.get(reverse('xss_lab:auditor'))
        self.assertContains(response, 'project root')

    def test_web_auditor_uses_the_same_engine_as_the_cli(self):
        expected = scan_path(settings.BASE_DIR)
        response = self.client.get(reverse('xss_lab:auditor'))
        self.assertEqual(response.context['total'], len(expected))
        self.assertEqual(
            {(f.rule_id, f.path, f.line_no) for f in response.context['findings']},
            {(f.rule_id, f.path, f.line_no) for f in expected},
        )

    def test_auditor_reports_exactly_four_genuine_findings_all_in_xss_lab(self):
        response = self.client.get(reverse('xss_lab:auditor'))
        self.assertEqual(response.context['total'], 4)
        for finding in response.context['findings']:
            self.assertTrue(finding.path.startswith('xss_lab/'))
