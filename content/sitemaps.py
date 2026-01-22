from django.contrib.sitemaps import Sitemap
from .models import Anime, Episode, Genre

class AnimeSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Anime.objects.all().order_by('-created_at')

    def lastmod(self, obj):
        return obj.created_at

class GenreSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Genre.objects.all().order_by('name')

class EpisodeSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return Episode.objects.select_related('season__anime').all().order_by('-created_at')

    def lastmod(self, obj):
        return obj.created_at
