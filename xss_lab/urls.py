from django.urls import path

from . import views

urlpatterns = [
    path('xss/', views.index, name='index'),

    path('xss/stored/vulnerable/', views.stored_vulnerable, name='stored_vulnerable'),
    path('xss/stored/secure/', views.stored_secure, name='stored_secure'),

    path('xss/reflected/vulnerable/', views.reflected_vulnerable, name='reflected_vulnerable'),
    path('xss/reflected/secure/', views.reflected_secure, name='reflected_secure'),

    path('xss/dom/vulnerable/', views.dom_vulnerable, name='dom_vulnerable'),
    path('xss/dom/secure/', views.dom_secure, name='dom_secure'),

    path('auditor/', views.auditor, name='auditor'),
    path('guide/', views.guide, name='guide'),
]
