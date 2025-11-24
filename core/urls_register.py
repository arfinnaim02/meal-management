"""
Separate URL configuration for user registration.

It’s kept distinct from the main URLconf to avoid name clashes and
simplify inclusion from the project-level urls.py.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.register_view, name='register'),
]