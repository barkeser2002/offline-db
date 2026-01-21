from django.db import migrations

def seed_genre_master_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    Badge.objects.get_or_create(
        slug='genre-master',
        defaults={
            'name': 'Genre Master',
            'description': 'Watched 10 different anime from the same genre.',
            'icon_url': '/static/badges/genre_master.png',
        }
    )

def remove_genre_master_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    Badge.objects.filter(slug='genre-master').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0018_seed_opinionated_badge'),
    ]

    operations = [
        migrations.RunPython(seed_genre_master_badge, remove_genre_master_badge),
    ]
