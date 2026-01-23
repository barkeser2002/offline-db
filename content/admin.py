from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
import requests
import re
import time
from django.contrib.admin import ModelAdmin
from .models import Anime, Season, Episode, FansubGroup, VideoFile, Subtitle

@admin.register(Anime)
class AnimeAdmin(ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)
    change_list_template = "admin/content/anime/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-jikan/', self.admin_site.admin_view(self.import_jikan_view), name='content_anime_import_jikan'),
        ]
        return my_urls + urls

    def import_jikan_view(self, request):
        if request.method == "POST":
            mal_id = request.POST.get('mal_id')
            if not mal_id:
                messages.error(request, "Please provide a MAL ID.")
                return redirect('admin:content_anime_import_jikan')

            try:
                # Fetch Anime Info
                headers = {'User-Agent': 'AniScrap/1.0 (admin-import)'}
                resp = requests.get(f'https://api.jikan.moe/v4/anime/{mal_id}', headers=headers)

                if resp.status_code != 200:
                    messages.error(request, f"Failed to fetch Anime. Status: {resp.status_code}")
                    return redirect('admin:content_anime_import_jikan')

                data = resp.json().get('data')
                if not data:
                    messages.error(request, "No data found for this ID.")
                    return redirect('admin:content_anime_import_jikan')

                title = data.get('title')
                synopsis = data.get('synopsis', '')
                image_url = data.get('images', {}).get('jpg', {}).get('large_image_url')

                anime, created = Anime.objects.get_or_create(
                    title=title,
                    defaults={
                        'synopsis': synopsis,
                        'cover_image': image_url
                    }
                )
                if not created:
                    # Update existing? Maybe just info.
                    anime.synopsis = synopsis
                    anime.cover_image = image_url
                    anime.save()

                # Fetch Episodes
                current_page = 1
                all_episodes = []
                while True:
                    # Rate limit safety
                    time.sleep(0.5)

                    ep_resp = requests.get(f'https://api.jikan.moe/v4/anime/{mal_id}/episodes?page={current_page}', headers=headers)
                    if ep_resp.status_code != 200:
                        break

                    ep_data = ep_resp.json()
                    items = ep_data.get('data', [])
                    all_episodes.extend(items)

                    pagination = ep_data.get('pagination', {})
                    if not pagination.get('has_next_page'):
                        break
                    current_page += 1

                if not all_episodes:
                     messages.warning(request, f"Anime '{title}' saved, but no episodes found.")
                     return redirect('admin:content_anime_changelist')

                # Create Season 1 (Default)
                season, _ = Season.objects.get_or_create(
                    anime=anime,
                    number=1,
                    defaults={'title': 'Season 1'}
                )

                count = 0
                for ep in all_episodes:
                    url = ep.get('url', '')
                    match = re.search(r'episode/(\d+)', url)
                    if match:
                        number = int(match.group(1))
                    else:
                        continue

                    ep_title = ep.get('title', f'Episode {number}')

                    Episode.objects.get_or_create(
                        season=season,
                        number=number,
                        defaults={
                            'title': ep_title
                        }
                    )
                    count += 1

                messages.success(request, f"Successfully imported '{title}' with {count} episodes.")
                return redirect('admin:content_anime_changelist')

            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
                return redirect('admin:content_anime_import_jikan')

        return render(request, 'admin/content/anime/import_jikan.html')

@admin.register(Season)
class SeasonAdmin(ModelAdmin):
    list_display = ('anime', 'number', 'title')
    list_filter = ('anime',)

@admin.register(Episode)
class EpisodeAdmin(ModelAdmin):
    list_display = ('season', 'number', 'title')
    list_select_related = ('season', 'season__anime')
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
