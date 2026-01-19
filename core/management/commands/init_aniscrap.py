from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from billing.models import SubscriptionPlan
from core.models import SiteSettings

class Command(BaseCommand):
    help = 'Initialize AniScrap project'

    def handle(self, *args, **options):
        self.stdout.write("Running migrations...")
        call_command('migrate')

        self.stdout.write("Creating superuser...")
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@aniscrap.com', '123123123')
            self.stdout.write(self.style.SUCCESS("Superuser 'admin' created."))
        else:
            self.stdout.write("Superuser 'admin' already exists.")

        self.stdout.write("Creating default subscription plan...")
        plan, created = SubscriptionPlan.objects.get_or_create(
            name='Premium Monthly',
            defaults={'price': 5.00, 'duration_days': 30}
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Plan created."))

        self.stdout.write("Initializing Site Settings...")
        SiteSettings.get_solo()

        self.stdout.write(self.style.SUCCESS("AniScrap initialized successfully! 🚀"))
