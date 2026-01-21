from django.db import migrations

def create_morning_glory_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    if not Badge.objects.filter(slug='morning-glory').exists():
        Badge.objects.create(
            slug='morning-glory',
            name='Morning Glory',
            description='Watched an episode between 6 AM and 9 AM',
            icon_url='/static/badges/morning-glory.png'
        )

def remove_morning_glory_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    Badge.objects.filter(slug='morning-glory').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0020_seed_speedster_badge'),
    ]

    operations = [
        migrations.RunPython(create_morning_glory_badge, remove_morning_glory_badge),
    ]
