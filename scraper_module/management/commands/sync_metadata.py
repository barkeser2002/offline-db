import asyncio
from django.core.management.base import BaseCommand
from asgiref.sync import sync_to_async
from scraper_module.services.jikan import jikan
from content.models import Anime
from django.db import transaction

class Command(BaseCommand):
    help = 'Syncs metadata from Jikan'

    def update_db(self, updates):
        with transaction.atomic():
            for title, synopsis, image_url in updates:
                anime, created = Anime.objects.update_or_create(
                    title=title,
                    defaults={
                        'synopsis': synopsis,
                        'cover_image': image_url
                    }
                )
                action = "Created" if created else "Updated"
                self.stdout.write(self.style.SUCCESS(f"{action}: {title}"))

    async def fetch_anime_data(self, mid, semaphore):
        try:
            async with semaphore:
                self.stdout.write(f"Fetching MAL ID {mid}...")
                data = await jikan.get_anime(mid)
                if data:
                    title = data.get('title')
                    synopsis = data.get('synopsis')
                    image_url = data.get('images', {}).get('jpg', {}).get('large_image_url')
                    return (title, synopsis, image_url)
                else:
                    self.stdout.write(self.style.WARNING(f"Could not fetch data for MAL ID {mid}"))
                    return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Exception fetching MAL ID {mid}: {e}"))
            return None

    async def sync_anime(self, mal_ids):
        semaphore = asyncio.Semaphore(5)  # Limit concurrent API calls

        # Process in chunks to avoid buffering everything in memory and to provide fault tolerance
        chunk_size = 50
        for i in range(0, len(mal_ids), chunk_size):
            chunk = mal_ids[i:i + chunk_size]
            tasks = [self.fetch_anime_data(mid, semaphore) for mid in chunk]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            valid_updates = []
            for res in results:
                if isinstance(res, tuple):
                    valid_updates.append(res)
                elif isinstance(res, Exception):
                    self.stdout.write(self.style.ERROR(f"Task exception: {res}"))

            if valid_updates:
                await sync_to_async(self.update_db, thread_sensitive=True)(valid_updates)

    def handle(self, *args, **options):
        self.stdout.write("Starting metadata sync from Jikan...")
        mal_ids = [1, 21, 1535] # Cowboy Bebop, One Piece, Death Note

        try:
            asyncio.run(self.sync_anime(mal_ids))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during sync: {e}"))

        self.stdout.write(self.style.SUCCESS("Sync complete."))
