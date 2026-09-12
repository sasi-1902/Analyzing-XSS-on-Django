"""
Views for the XSS security layer.

This app has no vulnerabilities or content of its own: every
demonstration here operates on the blog's real models (core.models.Post,
core.models.Comment) and the blog's real search logic
(core.views.search_queryset). Each vulnerability has exactly two views --
a "vulnerable" one that reproduces the unsafe pattern on purpose, and a
"secure" one that shows the fix -- so a learner can compare the same
underlying data rendered two different ways. Nothing here does anything
harmful on its own: there is no cookie theft, no external request, and
no exfiltration.

Run `python manage.py seed_demo` first so there is a real post/comments
to demonstrate Stored XSS against.
"""
from collections import Counter

from django.conf import settings
from django.shortcuts import redirect, render

from core.forms import CommentForm
from core.models import Comment, Post
from core.views import search_queryset
from core.xss_audit_rules import scan_path

# The demo post created by `seed_demo` that Stored XSS reads/writes
# comments on. Using a fixed, known slug keeps the demonstration
# reproducible without hard-coding a database id.
DEMO_POST_SLUG = 'mobile-commerce-and-everyday-shopping'


def _get_demo_post():
    return Post.objects.filter(slug=DEMO_POST_SLUG).first()


def index(request):
    """Concise overview: Stored / Reflected / DOM XSS and the Auditor."""
    return render(request, 'xss_lab/index.html', {'demo_post': _get_demo_post()})


def guide(request):
    """A walkthrough of using the running site: Blog, XSS Lab, and the Auditor."""
    return render(request, 'xss_lab/guide.html')


def auditor(request):
    """
    Read-only UI over the existing xss_audit scanner (core.xss_audit_rules).

    This always scans the project root (settings.BASE_DIR) -- it never
    accepts a filesystem path from the browser, so there is no way to
    point it at an arbitrary path via user input. The "Scan project"
    button is a plain GET to this same URL, which re-runs the scan;
    there is no separate code path or duplicated rule set.

    The absolute filesystem path is used internally to actually read the
    files, but is never sent to the browser -- the template only ever
    sees a neutral "project root" label and the repository-relative
    paths that Finding objects already carry.
    """
    findings = scan_path(settings.BASE_DIR)
    severity_counts = Counter(finding.severity for finding in findings)

    return render(request, 'xss_lab/auditor.html', {
        'findings': findings,
        'total': len(findings),
        'severity_counts': severity_counts,
        'scanned_root_label': 'project root (.)',
    })


def _stored_view(request, template_name):
    """
    Shared plumbing for the Stored XSS vulnerable/secure pages: both read
    and write comments on the exact same real blog post via the blog's
    own Comment model and CommentForm -- only the template differs in
    whether it applies |safe to the rendered comment content.
    """
    post = _get_demo_post()
    form = None
    comments = []

    if post is not None:
        form = CommentForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            Comment.objects.create(post=post, **form.cleaned_data)
            # Redirect back to the same page (POST/redirect/GET) so
            # refreshing the page does not resubmit the comment.
            return redirect(request.path)
        comments = post.comment_set.all()

    return render(request, template_name, {'post': post, 'comments': comments, 'form': form})


def stored_vulnerable(request):
    """
    VULNERABLE stored XSS.

    Comment content is rendered with the |safe filter, so a payload
    posted through this page's form executes every time anyone loads
    it -- for any visitor, not just the person who posted it.
    """
    return _stored_view(request, 'xss_lab/stored_vulnerable.html')


def stored_secure(request):
    """SECURE counterpart: the same post and comments, rendered without |safe."""
    return _stored_view(request, 'xss_lab/stored_secure.html')


def reflected_vulnerable(request):
    """
    VULNERABLE reflected XSS.

    Uses the blog's real search (core.views.search_queryset) for the
    `q` query parameter, then renders it back with |safe, so a payload
    such as ?q=<script>alert(1)</script> executes immediately for
    whoever opens the crafted link.
    """
    query = request.GET.get('q', '')
    posts = search_queryset(query)
    return render(request, 'xss_lab/reflected_vulnerable.html', {'query': query, 'posts': posts})


def reflected_secure(request):
    """SECURE counterpart: the same search, rendered with default auto-escaping."""
    query = request.GET.get('q', '')
    posts = search_queryset(query)
    return render(request, 'xss_lab/reflected_secure.html', {'query': query, 'posts': posts})


def dom_vulnerable(request):
    """
    VULNERABLE DOM-based XSS.

    A small search-preview widget: typing into the box (or loading the
    page with ?q=...) updates a live preview via JavaScript that reads
    the value and assigns it directly to `.innerHTML`.
    """
    return render(request, 'xss_lab/dom_vulnerable.html')


def dom_secure(request):
    """SECURE counterpart: the same live preview, assigned to `.textContent`."""
    return render(request, 'xss_lab/dom_secure.html')
