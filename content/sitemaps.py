from django.contrib.sitemaps import Sitemap
from .models import Anime

class AnimeSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Anime.objects.all().order_by('-created_at')

    def lastmod(self, obj):
        return obj.created_at
