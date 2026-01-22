from django.db import migrations

def seed_pilot_connoisseur_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    Badge.objects.get_or_create(
        slug='pilot-connoisseur',
        defaults={
            'name': 'Pilot Connoisseur',
            'description': 'Watched the first episode of 5 different anime series.',
            'icon_url': '/static/badges/pilot_connoisseur.png'
        }
    )

class Migration(migrations.Migration):

    dependencies = [
        ("users", "0024_seed_genre_savant_badge"),
    ]

    operations = [
        migrations.RunPython(seed_pilot_connoisseur_badge),
    ]
