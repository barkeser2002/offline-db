from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Anime, Episode, VideoKey

@admin.register(Anime)
class AnimeAdmin(ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Episode)
class EpisodeAdmin(ModelAdmin):
    list_display = ('anime', 'number', 'title', 'is_processed')
    list_filter = ('anime', 'is_processed')
    search_fields = ('anime__title', 'title')

@admin.register(VideoKey)
class VideoKeyAdmin(ModelAdmin):
    list_display = ('episode', 'is_active', 'created_at')
