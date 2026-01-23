# Generated manually

from django.db import migrations

def seed_specific_genre_badges(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    Badge.objects.get_or_create(
        slug='nightmare',
        defaults={
            'name': 'Nightmare',
            'description': 'Watched 5 Horror anime.',
            'icon_url': '/static/badges/nightmare.png'
        }
    )
    Badge.objects.get_or_create(
        slug='comedy-gold',
        defaults={
            'name': 'Comedy Gold',
            'description': 'Watched 5 Comedy anime.',
            'icon_url': '/static/badges/comedy_gold.png'
        }
    )

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0032_seed_tv_addict_and_ova_enthusiast'),
    ]

    operations = [
        migrations.RunPython(seed_specific_genre_badges),
    ]
