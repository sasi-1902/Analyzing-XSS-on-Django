"""
python manage.py xss_audit [path]

Heuristically scans source files for common XSS-prone code patterns:
Django's |safe filter and {% autoescape off %}, Python's mark_safe(),
and the JavaScript sinks .innerHTML, .outerHTML, document.write(), and
insertAdjacentHTML(). See core/xss_audit_rules.py for the rule set.

This is a small, dependency-light, regex-based scanner. It does NOT do
taint analysis, does NOT parse JavaScript or HTML, and does NOT prove a
finding is exploitable -- every finding requires human review.

The scanner's own implementation/tests are excluded from the default
scan, and an inline `xss-audit-ignore` marker can suppress a single
line of intentionally inert documentation/example code (see
core/xss_audit_rules.py for details on both).
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from core.xss_audit_rules import scan_path


class Command(BaseCommand):
    help = (
        'Heuristically scan source files for XSS-prone patterns '
        '(|safe, autoescape off, mark_safe, innerHTML/outerHTML assignment, '
        'document.write, insertAdjacentHTML). Findings require human review.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'path',
            nargs='?',
            default=None,
            help='Directory to scan (defaults to the project root).',
        )

    def handle(self, *args, **options):
        root = options['path'] or settings.BASE_DIR
        findings = scan_path(root)

        self.stdout.write(f'XSS audit: scanning {root}\n')

        if not findings:
            self.stdout.write(self.style.SUCCESS('No suspicious patterns found.'))
        else:
            for finding in findings:
                style = self.style.ERROR if finding.severity == 'HIGH' else self.style.WARNING
                self.stdout.write(style(
                    f'[{finding.severity}] {finding.rule_id}  {finding.path}:{finding.line_no}'
                ))
                self.stdout.write(f'    {finding.message}')
                self.stdout.write(f'    | {finding.snippet}')
            self.stdout.write(f'\n{len(findings)} finding(s).')

        self.stdout.write(
            '\nNote: this is a heuristic, regex-based scanner. It does not '
            'perform taint analysis or parse JavaScript, and no finding '
            'here proves the code is actually exploitable. Review each '
            'finding by hand.'
        )
