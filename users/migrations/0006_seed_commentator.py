from django.db import migrations

def create_commentator_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    if not Badge.objects.filter(slug='commentator').exists():
        Badge.objects.create(
            slug='commentator',
            name='Commentator',
            description='Posted 50 chat messages',
            icon_url='/static/badges/commentator.png'
        )

def remove_commentator_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    Badge.objects.filter(slug='commentator').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_seed_night_owl'),
    ]

    operations = [
        migrations.RunPython(create_commentator_badge, remove_commentator_badge),
    ]
