"""
WSGI config for meal_manager project.

This file exposes the WSGI callable as a module-level variable named
``application``. It is used by WSGI servers such as Gunicorn or uWSGI
to run your Django application.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application  # type: ignore


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_manager.settings')

application = get_wsgi_application()
