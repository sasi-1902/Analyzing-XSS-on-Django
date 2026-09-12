"""
Tests for the xss_audit heuristic scanner (core/xss_audit_rules.py).

These use small, throwaway fixture files instead of scanning the real
project, so the tests stay correct regardless of future edits to the
lab templates.
"""
import tempfile
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from core.xss_audit_rules import EXCLUDED_PATHS, scan_path


class ScanVulnerablePatternsTests(SimpleTestCase):
    """Each representative vulnerable pattern should be detected."""

    def _scan_single_file(self, filename, content):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / filename
            path.write_text(content, encoding='utf-8')
            return scan_path(tmp)

    def test_detects_template_safe_filter(self):
        findings = self._scan_single_file(
            'template.html', '<p>{{ comment.content|safe }}</p>\n'
        )
        rule_ids = [f.rule_id for f in findings]
        self.assertIn('DJX001', rule_ids)

    def test_detects_autoescape_off(self):
        findings = self._scan_single_file(
            'template.html', '{% autoescape off %}{{ value }}{% endautoescape %}\n'
        )
        rule_ids = [f.rule_id for f in findings]
        self.assertIn('DJX002', rule_ids)

    def test_detects_mark_safe(self):
        findings = self._scan_single_file(
            'views.py', 'from django.utils.safestring import mark_safe\n'
            'html = mark_safe(user_input)\n'
        )
        rule_ids = [f.rule_id for f in findings]
        self.assertIn('DJX003', rule_ids)

    def test_detects_inner_html_assignment(self):
        findings = self._scan_single_file(
            'app.js', "document.getElementById('x').innerHTML = query;\n"
        )
        rule_ids = [f.rule_id for f in findings]
        self.assertIn('DOMX001', rule_ids)

    def test_detects_outer_html_assignment(self):
        findings = self._scan_single_file(
            'app.js', "el.outerHTML = query;\n"
        )
        rule_ids = [f.rule_id for f in findings]
        self.assertIn('DOMX002', rule_ids)

    def test_detects_document_write(self):
        findings = self._scan_single_file(
            'app.js', "document.write(query);\n"
        )
        rule_ids = [f.rule_id for f in findings]
        self.assertIn('DOMX003', rule_ids)

    def test_detects_insert_adjacent_html(self):
        findings = self._scan_single_file(
            'app.js', "el.insertAdjacentHTML('beforeend', query);\n"
        )
        rule_ids = [f.rule_id for f in findings]
        self.assertIn('DOMX004', rule_ids)

    def test_reports_correct_file_and_line_number(self):
        findings = self._scan_single_file(
            'template.html',
            '<p>fine</p>\n<p>also fine</p>\n<p>{{ value|safe }}</p>\n',
        )
        matches = [f for f in findings if f.rule_id == 'DJX001']
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].line_no, 3)
        self.assertEqual(matches[0].path, 'template.html')


class ScanSafePatternsTests(SimpleTestCase):
    """Representative safe/normal code should never be flagged."""

    def _scan_single_file(self, filename, content):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / filename
            path.write_text(content, encoding='utf-8')
            return scan_path(tmp)

    def test_default_escaped_template_output_is_not_flagged(self):
        findings = self._scan_single_file(
            'template.html', '<p>{{ comment.content }}</p>\n'
        )
        self.assertEqual(findings, [])

    def test_text_content_assignment_is_not_flagged(self):
        findings = self._scan_single_file(
            'app.js', "document.getElementById('x').textContent = query;\n"
        )
        self.assertEqual(findings, [])

    def test_plain_python_string_formatting_is_not_flagged(self):
        findings = self._scan_single_file(
            'views.py', 'message = "hello {}".format(name)\n'
        )
        self.assertEqual(findings, [])


class IgnoreAnnotationTests(SimpleTestCase):
    """The `xss-audit-ignore` marker suppresses exactly the line it is on."""

    def _scan_single_file(self, filename, content):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / filename
            path.write_text(content, encoding='utf-8')
            return scan_path(tmp)

    def test_same_line_marker_suppresses_the_finding(self):
        findings = self._scan_single_file(
            'template.html',
            '<p>{{ value|safe }}</p>  <!-- xss-audit-ignore: illustrative -->\n',
        )
        self.assertEqual(findings, [])

    def test_marker_on_previous_line_suppresses_the_finding(self):
        findings = self._scan_single_file(
            'template.html',
            '<!-- xss-audit-ignore: illustrative -->\n<p>{{ value|safe }}</p>\n',
        )
        self.assertEqual(findings, [])

    def test_unmarked_matching_line_is_still_flagged(self):
        findings = self._scan_single_file(
            'template.html', '<p>{{ value|safe }}</p>\n'
        )
        self.assertEqual(len(findings), 1)

    def test_marker_does_not_suppress_an_unrelated_later_line(self):
        # The marker only reaches the line it is on and the one right
        # after it -- it must not blanket-suppress the rest of the file.
        findings = self._scan_single_file(
            'template.html',
            '<!-- xss-audit-ignore: illustrative -->\n'
            '<p>{{ value|safe }}</p>\n'
            '<p>{{ other|safe }}</p>\n',
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].line_no, 3)


class ScanExclusionsTests(SimpleTestCase):
    """The scanner must not report on its own implementation/tests."""

    def test_excluded_paths_constant_matches_the_scanner_files(self):
        self.assertIn('core/xss_audit_rules.py', EXCLUDED_PATHS)
        self.assertIn('core/management/commands/xss_audit.py', EXCLUDED_PATHS)
        self.assertIn('core/test_xss_audit.py', EXCLUDED_PATHS)

    def test_default_project_scan_excludes_scanner_implementation(self):
        findings = scan_path(settings.BASE_DIR)
        paths = {f.path for f in findings}
        self.assertFalse(paths & EXCLUDED_PATHS)

    def test_default_project_scan_flags_only_xss_lab_code(self):
        # The reference application (core/users) is safe by default and
        # must have zero findings; everything reported should point at
        # the intentionally vulnerable xss_lab pages.
        findings = scan_path(settings.BASE_DIR)
        self.assertTrue(findings, 'expected the vulnerable lab pages to produce findings')
        for finding in findings:
            self.assertTrue(
                finding.path.startswith('xss_lab/'),
                f'unexpected finding outside xss_lab/: {finding.path}:{finding.line_no}',
            )

    def test_excluded_file_can_still_be_scanned_when_targeted_directly(self):
        # Exclusion only applies to the default project-root scan; a
        # narrower explicit path should still be scanned normally.
        target = settings.BASE_DIR / 'core' / 'xss_audit_rules.py'
        findings = scan_path(target.parent)
        # Scanning just the `core` directory does not hit the project-root
        # exclusion list (paths are relative to the scanned root, not to
        # BASE_DIR), so the rule table's own literal strings are found.
        paths = {f.path for f in findings}
        self.assertIn('xss_audit_rules.py', paths)
