"""
URL configuration for the meal_manager project.

Defines URL patterns for the project, delegating application-specific
patterns to the ``core`` app. Includes routes for the Django admin
interface and authentication views.
"""

from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    # Authentication views
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Registration handled in core app
    path('register/', include('core.urls_register')),
    # Core application
    path('', include('core.urls')),
]