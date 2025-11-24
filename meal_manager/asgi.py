"""
ASGI config for meal_manager project.

This file exposes the ASGI callable as a module-level variable named
``application``. It is used by ASGI servers like Daphne or Uvicorn to
serve your Django application.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application  # type: ignore


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_manager.settings')

application = get_asgi_application()
