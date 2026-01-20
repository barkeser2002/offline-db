from django.db import migrations

def create_night_owl_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    if not Badge.objects.filter(slug='night-owl').exists():
        Badge.objects.create(
            slug='night-owl',
            name='Night Owl',
            description='Watched an episode between 2 AM and 5 AM',
            icon_url='/static/badges/night-owl.png'
        )

def remove_night_owl_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    Badge.objects.filter(slug='night-owl').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_notification'),
    ]

    operations = [
        migrations.RunPython(create_night_owl_badge, remove_night_owl_badge),
    ]
