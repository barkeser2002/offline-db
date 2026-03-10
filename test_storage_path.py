import os
import django
from django.conf import settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aniscrap_core.settings')
django.setup()

from core.storage import LocalStorage

storage = LocalStorage()
print("Base path:", storage.base_path)
print("Join:", os.path.join(storage.base_path, "../../../../../etc/passwd"))
