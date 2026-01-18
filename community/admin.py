from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import FansubGroup, Subtitle

@admin.register(FansubGroup)
class FansubGroupAdmin(ModelAdmin):
    list_display = ('name',)

@admin.register(Subtitle)
class SubtitleAdmin(ModelAdmin):
    list_display = ('episode', 'language', 'fansub_group')
