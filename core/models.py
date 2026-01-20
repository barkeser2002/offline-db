from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Blog(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class SupportTicket(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.subject}"

class AdSlot(models.Model):
    position = models.CharField(max_length=50, unique=True, help_text=_("e.g. 'header', 'sidebar', 'footer'"))
    code = models.TextField(help_text=_("HTML/JS code for the ad"))
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.position

class SiteSettings(models.Model):
    deepl_api_keys = models.TextField(default="", help_text=_("Comma separated DeepL API keys"))
    maintenance_mode = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Site Configuration"

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            return # Singleton
        return super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class ChatMessage(models.Model):
    room_name = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_messages')
    username = models.CharField(max_length=255, help_text=_("Username used at the time of messaging"))
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.username} in {self.room_name}: {self.message[:20]}"
