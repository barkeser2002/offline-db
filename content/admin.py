from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Anime, Season, Episode, FansubGroup, VideoFile, Subtitle

@admin.register(Anime)
class AnimeAdmin(ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)

@admin.register(Season)
class SeasonAdmin(ModelAdmin):
    list_display = ('anime', 'number', 'title')
    list_filter = ('anime',)

@admin.register(Episode)
class EpisodeAdmin(ModelAdmin):
    list_display = ('season', 'number', 'title')
    list_filter = ('season__anime', 'season')
    search_fields = ('title', 'season__anime__title')

@admin.register(FansubGroup)
class FansubGroupAdmin(ModelAdmin):
    list_display = ('name', 'website', 'owner')
    search_fields = ('name',)

@admin.register(VideoFile)
class VideoFileAdmin(ModelAdmin):
    list_display = ('episode', 'quality', 'fansub_group', 'created_at')
    list_filter = ('quality', 'fansub_group')

@admin.register(Subtitle)
class SubtitleAdmin(ModelAdmin):
    list_display = ('episode', 'lang', 'fansub_group')
    list_filter = ('lang',)
