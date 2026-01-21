from django.db import migrations

def seed_opinionated_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    Badge.objects.get_or_create(
        slug='opinionated',
        defaults={
            'name': 'Opinionated',
            'description': 'Wrote 5 reviews.',
            'icon_url': '/static/badges/opinionated.png',
        }
    )

def remove_opinionated_badge(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    Badge.objects.filter(slug='opinionated').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0017_seed_critic_badge'),
    ]

    operations = [
        migrations.RunPython(seed_opinionated_badge, remove_opinionated_badge),
    ]
