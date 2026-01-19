import psutil
from django.utils.translation import gettext_lazy as _
from content.models import Anime, Episode
from billing.models import ShopierPayment
from django.db.models import Sum

def dashboard_callback(request, context):
    """
    Callback to populate the Unfold admin dashboard.
    """

    # Server Stats
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent

    # Content Stats
    anime_count = Anime.objects.count()
    episode_count = Episode.objects.count()

    # Revenue Stats
    total_revenue = ShopierPayment.objects.filter(status='success').aggregate(Sum('amount'))['amount__sum'] or 0

    # Unfold expects us to just modify context or return it.
    # We can pass data to be used in the custom dashboard template if we had one.
    # But Unfold also supports 'kpi' if we configure it in settings properly or just pass variables.
    # We'll pass raw data and assume the template renders it or we use Unfold widgets if available in views.

    context.update({
        "dashboard_stats": {
            "cpu": cpu_usage,
            "ram": ram_usage,
            "anime_count": anime_count,
            "episode_count": episode_count,
            "total_revenue": total_revenue,
        }
    })

    return context
