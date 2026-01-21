from django.db import migrations

def create_weekend_warrior_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    if not Badge.objects.filter(slug='weekend-warrior').exists():
        Badge.objects.create(
            slug='weekend-warrior',
            name='Weekend Warrior',
            description='Watched 5 episodes on a single weekend day',
            icon_url='/static/badges/weekend-warrior.png'
        )

def remove_weekend_warrior_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    Badge.objects.filter(slug='weekend-warrior').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_seed_marathoner'),
    ]

    operations = [
        migrations.RunPython(create_weekend_warrior_badge, remove_weekend_warrior_badge),
    ]
