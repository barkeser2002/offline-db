import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aniscrap_core.settings')
django.setup()

from users.models import Badge

badges = [
    {'name': 'Critic', 'slug': 'critic', 'description': 'Test'},
    {'name': 'Collector', 'slug': 'collector', 'description': 'Test'}
]

for b in badges:
    Badge.objects.get_or_create(slug=b['slug'], defaults={'name': b['name'], 'description': b['description']})

print("Badges created")
