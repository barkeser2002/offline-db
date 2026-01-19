from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    is_premium = models.BooleanField(default=False, verbose_name=_("Premium Status"))

    def __str__(self):
        return self.username

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_("Balance"))

    def __str__(self):
        return f"{self.user.username}'s Wallet: {self.balance:.2f}"

class WatchLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_logs')
    episode = models.ForeignKey('content.Episode', on_delete=models.CASCADE, related_name='watch_logs')
    duration = models.PositiveIntegerField(help_text=_("Duration watched in seconds"))
    watched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} watched {self.episode} for {self.duration}s"

class Badge(models.Model):
    slug = models.SlugField(unique=True, help_text=_("Unique identifier for the badge logic"))
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')
        verbose_name = _("User Badge")
        verbose_name_plural = _("User Badges")

    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
