from django.db import migrations

def create_party_badges(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')

    if not Badge.objects.filter(slug='party-host').exists():
        Badge.objects.create(
            slug='party-host',
            name='Party Host',
            description='Hosted 5 Watch Parties',
            icon_url='/static/badges/party-host.png'
        )

    if not Badge.objects.filter(slug='party-animal').exists():
        Badge.objects.create(
            slug='party-animal',
            name='Party Animal',
            description='Participated in 5 different Watch Parties',
            icon_url='/static/badges/party-animal.png'
        )

def remove_party_badges(apps, schema_editor):
    Badge = apps.get_model('users', 'Badge')
    Badge.objects.filter(slug__in=['party-host', 'party-animal']).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0021_seed_morning_glory_badge'),
    ]

    operations = [
        migrations.RunPython(create_party_badges, remove_party_badges),
    ]
