from django.db import migrations

def create_content_creator_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')

    if not Badge.objects.filter(slug='content-creator').exists():
        Badge.objects.create(
            slug='content-creator',
            name='Content Creator',
            description='Uploaded 5 videos to the platform.',
            icon_url='/static/badges/content-creator.png'
        )

def remove_content_creator_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    Badge.objects.filter(slug='content-creator').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0022_seed_party_badges'),
    ]

    operations = [
        migrations.RunPython(create_content_creator_badge, remove_content_creator_badge),
    ]
