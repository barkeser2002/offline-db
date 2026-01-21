from django.db import migrations

def seed_streak_master_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    Badge.objects.get_or_create(
        slug='streak-master',
        defaults={
            'name': 'Streak Master',
            'description': 'Watched anime for 7 consecutive days.',
            'icon_url': 'https://img.icons8.com/color/48/000000/fire-element.png'
        }
    )

def remove_streak_master_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    Badge.objects.filter(slug='streak-master').delete()

class Migration(migrations.Migration):

    dependencies = [
        ("users", "0014_seed_loyal_fan_badge"),
    ]

    operations = [
        migrations.RunPython(seed_streak_master_badge, remove_streak_master_badge),
    ]
