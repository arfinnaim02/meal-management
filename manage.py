#!/usr/bin/env python3
"""
manage.py
-------------
Entry point for Django administrative tasks.

This script allows you to perform a variety of maintenance operations for
your project, such as running the development server, applying
migrations, creating new applications, and more. It defers most of the
work to Django’s management utility.

To learn more about the available commands, run:

    ./manage.py help
"""

import os
import sys


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_manager.settings')
    try:
        from django.core.management import execute_from_command_line  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()