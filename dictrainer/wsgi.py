"""
WSGI config for dictrainer project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from django_docker_helpers.files import collect_static
from django_docker_helpers.db import migrate, ensure_caches_alive, ensure_databases_alive
from django_docker_helpers.utils import is_production, is_dockerized

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dictrainer.settings")

if is_dockerized():
    ensure_databases_alive()
    ensure_caches_alive()

    if is_production():
        collect_static()
        migrate()

application = get_wsgi_application()
