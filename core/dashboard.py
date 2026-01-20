import json
import psutil
from datetime import timedelta
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from content.models import Anime, Episode, VideoFile
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

    # Bandwidth Saved Calculation (Assume H.265 saves ~50% compared to H.264)
    # So saved amount = size of H.265 files (approx).
    total_h265_size_bytes = VideoFile.objects.aggregate(Sum('file_size_bytes'))['file_size_bytes__sum'] or 0
    bandwidth_saved_gb = round(total_h265_size_bytes / (1024 * 1024 * 1024), 2)

    # Graph Data: Last 7 Days
    today = timezone.now().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    chart_labels = [day.strftime("%Y-%m-%d") for day in last_7_days]
    chart_data = []

    for day in last_7_days:
        daily_size = VideoFile.objects.filter(
            created_at__date=day
        ).aggregate(Sum('file_size_bytes'))['file_size_bytes__sum'] or 0
        chart_data.append(round(daily_size / (1024 * 1024 * 1024), 2))

    # Revenue Stats
    total_revenue = ShopierPayment.objects.filter(status='success').aggregate(Sum('amount'))['amount__sum'] or 0

    # Chart.js Data Structure
    bandwidth_chart_json = json.dumps({
        "labels": chart_labels,
        "datasets": [
            {
                "label": str(_("Bandwidth Saved (GB)")),
                "data": chart_data,
                "backgroundColor": "rgba(59, 130, 246, 0.5)",
                "borderColor": "rgba(59, 130, 246, 1)",
                "borderWidth": 1
            }
        ]
    })

    context.update({
        "dashboard_stats": {
            "cpu": cpu_usage,
            "ram": ram_usage,
            "anime_count": anime_count,
            "episode_count": episode_count,
            "bandwidth_saved_gb": bandwidth_saved_gb,
            "bandwidth_chart": bandwidth_chart_json,
            "total_revenue": total_revenue,
        }
    })

    return context
