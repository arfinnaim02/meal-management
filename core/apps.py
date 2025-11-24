"""
Application configuration for the core app.

Defines application metadata used by Django to configure
models, signals, and default settings.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'