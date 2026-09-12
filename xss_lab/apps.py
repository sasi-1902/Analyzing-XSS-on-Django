from django.apps import AppConfig


class XssLabConfig(AppConfig):
    """
    XSS security layer, attached to the Django blog under /xss/ (see
    blog/urls.py). Every view here demonstrates a vulnerability or its
    secure counterpart using the blog's own real posts, comments and
    search (core.models, core.views) -- it has no models or content of
    its own. See xss_lab/views.py for details.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'xss_lab'
    verbose_name = 'XSS Lab'
