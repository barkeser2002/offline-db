import asyncio
from django.core.management.base import BaseCommand
from asgiref.sync import sync_to_async
from scraper_module.services.jikan import jikan
from content.models import Anime

class Command(BaseCommand):
    help = 'Syncs metadata from Jikan'

    def update_db(self, title, synopsis, image_url):
        anime, created = Anime.objects.update_or_create(
            title=title,
            defaults={
                'synopsis': synopsis,
                'cover_image': image_url
            }
        )
        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action}: {title}"))

    async def sync_anime(self, mal_ids):
        for mid in mal_ids:
            self.stdout.write(f"Fetching MAL ID {mid}...")
            data = await jikan.get_anime(mid)
            if data:
                title = data.get('title')
                synopsis = data.get('synopsis')
                image_url = data.get('images', {}).get('jpg', {}).get('large_image_url')

                await sync_to_async(self.update_db, thread_sensitive=True)(title, synopsis, image_url)
            else:
                self.stdout.write(self.style.WARNING(f"Could not fetch data for MAL ID {mid}"))

    def handle(self, *args, **options):
        self.stdout.write("Starting metadata sync from Jikan...")
        mal_ids = [1, 21, 1535] # Cowboy Bebop, One Piece, Death Note

        try:
            asyncio.run(self.sync_anime(mal_ids))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during sync: {e}"))

        self.stdout.write(self.style.SUCCESS("Sync complete."))
