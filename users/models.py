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
        return f"{self.user.username}'s Wallet: {self.balance}"

class WatchLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_logs')
    episode = models.ForeignKey('content.Episode', on_delete=models.CASCADE, related_name='watch_logs')
    duration = models.PositiveIntegerField(help_text=_("Duration watched in seconds"))
    watched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} watched {self.episode} for {self.duration}s"
