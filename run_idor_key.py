import os
import django
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aniscrap_core.settings")
django.setup()
