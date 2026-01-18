import psutil
from django.utils.translation import gettext_lazy as _
from content.models import Anime, Episode
from community.models import FansubGroup

def dashboard_callback(request):
    # Server Health
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent

    # Context data for the dashboard
    context = {
        "kpi": [
            {
                "title": _("Total Anime"),
                "metric": Anime.objects.count(),
                "footer": _("Titles in database"),
            },
            {
                "title": _("Total Episodes"),
                "metric": Episode.objects.count(),
                "footer": _("Episodes uploaded"),
            },
            {
                "title": _("Server CPU"),
                "metric": f"{cpu_usage}%",
                "footer": _("Real-time load"),
            },
            {
                "title": _("Server RAM"),
                "metric": f"{ram_usage}%",
                "footer": _("Real-time usage"),
            },
        ],
        "navigation": [
            {"title": _("Management"), "link": "/admin/content/anime/", "icon": "monitor"},
            {"title": _("Community"), "link": "/admin/community/fansubgroup/", "icon": "users"},
        ]
    }
    return context
