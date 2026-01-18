from django.db import models

class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default="AniScrap")
    contact_email = models.EmailField(default="info@bariskeser.com")
    abuse_email = models.EmailField(default="abuse@bariskeser.com")
    dmca_email = models.EmailField(default="dmca@bariskeser.com")
    maintenance_mode = models.BooleanField(default=False)

    def __str__(self):
        return "Site Settings"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SiteSettings.objects.exists():
             return SiteSettings.objects.first()
        return super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj
