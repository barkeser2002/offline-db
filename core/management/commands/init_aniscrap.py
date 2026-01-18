from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from core.models import SiteSettings

class Command(BaseCommand):
    help = 'Initialize AniScrap Project'

    def handle(self, *args, **kwargs):
        self.stdout.write("Running migrations...")
        call_command('migrate', interactive=False)

        self.stdout.write("Creating superuser...")
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'info@bariskeser.com', '123123123')
            self.stdout.write(self.style.SUCCESS("Superuser 'admin' created."))
        else:
            self.stdout.write("Superuser 'admin' already exists.")

        self.stdout.write("Initializing Site Settings...")
        settings = SiteSettings.get_settings()
        settings.site_name = "AniScrap"
        settings.contact_email = "info@bariskeser.com"
        settings.abuse_email = "abuse@bariskeser.com"
        settings.dmca_email = "dmca@bariskeser.com"
        settings.save()
        self.stdout.write(self.style.SUCCESS("Site Settings initialized."))
