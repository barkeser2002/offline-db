from django.db import migrations

def seed_speedster_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    Badge.objects.get_or_create(
        slug='speedster',
        defaults={
            'name': 'Speedster',
            'description': 'Watched 3 episodes in less than 1 hour.',
            'icon_url': '/static/badges/speedster.png',
        }
    )

def remove_speedster_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    Badge.objects.filter(slug='speedster').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_seed_genre_master_badge'),
    ]

    operations = [
        migrations.RunPython(seed_speedster_badge, remove_speedster_badge),
    ]
