"""
Heuristic, regex-based rules for the `xss_audit` management command.

This module deliberately does NOT do taint analysis, does NOT parse
JavaScript or HTML, and does NOT crawl a browser. It scans source files
line by line for a short, fixed list of suspicious textual patterns.

A finding means "this line matches a pattern that is commonly involved
in XSS bugs" -- nothing more. It does not prove the code path is
reachable with attacker-controlled input, and it does not prove the
finding is exploitable. Every finding requires human review.

Two things are deliberately kept out of the default scan so the output
stays focused on genuine application findings:

- EXCLUDED_PATHS: the scanner's own implementation and tests. Scanning
  the tool's own source would otherwise flag its rule table (which
  necessarily contains strings like "|safe" and ".innerHTML") as
  findings about itself.
- IGNORE_MARKER: an inline opt-out for lines that are inert
  documentation/example code (e.g. a `<pre><code>` comparison snippet
  on a lab page showing what the vulnerable line looks like), not live
  application code. Put the literal text "xss-audit-ignore" either on
  the flagged line itself or on the line immediately above it. This
  never suppresses a whole file or directory, only the one line it is
  attached to, and it is not used anywhere on a real vulnerable sink.
"""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

# Directories that are never worth scanning: dependency/build/VCS noise.
SKIP_DIR_NAMES = {
    '.git', '__pycache__', '.venv', 'venv', 'env',
    'node_modules', 'staticfiles', 'media', '.idea', '.vscode',
}

# Repo-relative (forward-slash) paths excluded from the default scan
# because they are the scanner's own implementation/tests, not
# application code. This only matches these exact paths -- it does not
# hide an entire directory, and scanning a narrower path explicitly
# (e.g. `manage.py xss_audit core/xss_audit_rules.py`) still works.
EXCLUDED_PATHS = {
    'core/xss_audit_rules.py',
    'core/management/commands/xss_audit.py',
    'core/test_xss_audit.py',
}

# Inline suppression marker for intentionally inert documentation/example
# lines (see module docstring). Never use this on a real vulnerable sink.
IGNORE_MARKER = 'xss-audit-ignore'

TEMPLATE_EXTENSIONS = {'.html', '.htm'}
PYTHON_EXTENSIONS = {'.py'}
JS_EXTENSIONS = {'.js'}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    path: str  # project-relative, forward-slash separated
    line_no: int
    message: str
    snippet: str


# Rules are (rule_id, severity, compiled pattern, message) tuples so the
# whole rule set is readable at a glance, top to bottom.

# DJX*: server-side Django patterns that disable autoescaping.
TEMPLATE_RULES = [
    (
        'DJX001', 'HIGH',
        re.compile(r'\|\s*safe\b'),
        'Django template |safe filter disables autoescaping for this value.',
    ),
    (
        'DJX002', 'HIGH',
        re.compile(r'\{%\s*autoescape\s+off\s*%\}'),
        '{% autoescape off %} disables autoescaping for this whole block.',
    ),
]

PYTHON_RULES = [
    (
        'DJX003', 'HIGH',
        re.compile(r'\bmark_safe\s*\('),
        'mark_safe() marks a string safe for HTML, bypassing autoescaping.',
    ),
]

# DOMX*: client-side JavaScript sinks commonly used for DOM-based XSS.
DOM_RULES = [
    (
        'DOMX001', 'HIGH',
        re.compile(r'\.innerHTML\s*(?:=(?!=)|\+=)'),
        'Assignment to .innerHTML can execute injected markup.',
    ),
    (
        'DOMX002', 'HIGH',
        re.compile(r'\.outerHTML\s*(?:=(?!=)|\+=)'),
        'Assignment to .outerHTML can execute injected markup.',
    ),
    (
        'DOMX003', 'MEDIUM',
        re.compile(r'\bdocument\.write(?:ln)?\s*\('),
        'document.write()/writeln() can inject and execute markup.',
    ),
    (
        'DOMX004', 'MEDIUM',
        re.compile(r'\.insertAdjacentHTML\s*\('),
        'insertAdjacentHTML() can execute injected markup.',
    ),
]


def _iter_source_files(root: Path):
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.relative_to(root).as_posix() in EXCLUDED_PATHS:
            continue
        yield path


def _scan_lines(path: Path, root: Path, rules) -> List[Finding]:
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return []

    rel = path.relative_to(root).as_posix()
    lines = text.splitlines()
    findings = []
    for line_no, line in enumerate(lines, start=1):
        if IGNORE_MARKER in line:
            continue
        previous_line = lines[line_no - 2] if line_no >= 2 else ''
        if IGNORE_MARKER in previous_line:
            continue

        for rule_id, severity, pattern, message in rules:
            if pattern.search(line):
                findings.append(Finding(
                    rule_id=rule_id,
                    severity=severity,
                    path=rel,
                    line_no=line_no,
                    message=message,
                    snippet=line.strip()[:120],
                ))
    return findings


def scan_path(root) -> List[Finding]:
    """
    Scan `root` for suspicious XSS-related patterns.

    Returns a list of Finding objects sorted by path, then line number.
    This is a heuristic textual scan only -- see the module docstring.
    """
    root = Path(root).resolve()
    findings: List[Finding] = []

    for path in _iter_source_files(root):
        suffix = path.suffix.lower()
        if suffix in TEMPLATE_EXTENSIONS:
            # Templates can contain both Django tags and inline <script>.
            findings += _scan_lines(path, root, TEMPLATE_RULES)
            findings += _scan_lines(path, root, DOM_RULES)
        elif suffix in PYTHON_EXTENSIONS:
            findings += _scan_lines(path, root, PYTHON_RULES)
        elif suffix in JS_EXTENSIONS:
            findings += _scan_lines(path, root, DOM_RULES)

    findings.sort(key=lambda f: (f.path, f.line_no, f.rule_id))
    return findings
