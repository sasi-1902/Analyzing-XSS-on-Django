"""blog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/

The Django blog (core/users) is the primary application, mounted at the
site root. The XSS security layer (xss_lab) is attached under /xss/,
alongside the standalone /auditor/ and /guide/ pages -- it demonstrates
vulnerabilities using the blog's own posts, comments and search rather
than a separate parallel application.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # The Django blog: home, posts, comments, search. This is the primary
    # application and requires no login to read.
    path('', include(('core.urls', 'core'), namespace='core')),
    path('users/', include(('users.urls', 'users'), namespace='users')),

    # XSS security layer: an overview page, vulnerable/secure
    # demonstrations built on the blog's real models, and the Auditor.
    path('', include(('xss_lab.urls', 'xss_lab'), namespace='xss_lab')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
