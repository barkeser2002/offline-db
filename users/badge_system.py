from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Count, Q
from core.models import ChatMessage
from content.models import Subscription, Review, VideoFile, Anime, Genre, Episode
from apps.watchparty.models import Room
from .models import WatchLog, UserBadge, Badge

class BadgeStrategy:
    """
    Abstract base class for badge awarding strategies.
    """
    def check(self, user, awarded_slugs, all_badges, new_badges, cache=None):
        """
        Checks if the user qualifies for badges handled by this strategy.
        Appends new UserBadge instances to new_badges list.
        """
        raise NotImplementedError

    def _award(self, user, slug, awarded_slugs, all_badges, new_badges):
        """
        Helper to award a badge if not already awarded.
        """
        if slug in all_badges and slug not in awarded_slugs:
            new_badges.append(UserBadge(user=user, badge=all_badges[slug]))
            awarded_slugs.add(slug)

class ReviewBadgeStrategy(BadgeStrategy):
    def check(self, user, awarded_slugs, all_badges, new_badges, cache=None):
        needed = False
        for slug in ['critic', 'opinionated', 'review-guru', 'star-power']:
            if slug not in awarded_slugs:
                needed = True
                break

        if not needed:
            return

        stats = Review.objects.filter(user=user).aggregate(
            total=Count('id'),
            perfect=Count('id', filter=Q(rating=10))
        )
        total_reviews = stats['total'] or 0
        perfect_reviews = stats['perfect'] or 0

        # 0. Critic: Wrote first review.
        if 'critic' not in awarded_slugs:
            if total_reviews >= 1:
                self._award(user, 'critic', awarded_slugs, all_badges, new_badges)

        # 0.5. Opinionated: Wrote 5 reviews.
        if 'opinionated' not in awarded_slugs:
            if total_reviews >= 5:
                self._award(user, 'opinionated', awarded_slugs, all_badges, new_badges)

        # 24. Review Guru: Wrote 20 reviews.
        if 'review-guru' not in awarded_slugs:
            if total_reviews >= 20:
                self._award(user, 'review-guru', awarded_slugs, all_badges, new_badges)

        # 25. Star Power: Rated 5 anime with a perfect 10/10 score.
        if 'star-power' not in awarded_slugs:
            if perfect_reviews >= 5:
                self._award(user, 'star-power', awarded_slugs, all_badges, new_badges)

class WatchTimeBadgeStrategy(BadgeStrategy):
    def check(self, user, awarded_slugs, all_badges, new_badges, cache=None):
        # Optimization: Fetch 24h count once for both binge-watcher and marathon-runner
        if 'binge-watcher' not in awarded_slugs or 'marathon-runner' not in awarded_slugs:
            last_24h = timezone.now() - timedelta(hours=24)
            count_24h = WatchLog.objects.filter(user=user, watched_at__gte=last_24h).values('episode').distinct().count()

            # 1. Binge Watcher: Watched 5+ episodes in the last 24 hours.
            if 'binge-watcher' not in awarded_slugs and count_24h >= 5:
                self._award(user, 'binge-watcher', awarded_slugs, all_badges, new_badges)

            # 32. Marathon Runner: Watched 12+ episodes in the last 24 hours.
            if 'marathon-runner' not in awarded_slugs and count_24h >= 12:
                self._award(user, 'marathon-runner', awarded_slugs, all_badges, new_badges)

        # 1.1 Weekend Warrior: Watched 5+ episodes on a single weekend day.
        if 'weekend-warrior' not in awarded_slugs:
            today = timezone.now().date()
            if today.weekday() in [5, 6]:
                count = WatchLog.objects.filter(user=user, watched_at__date=today).values('episode').distinct().count()
                if count >= 5:
                    self._award(user, 'weekend-warrior', awarded_slugs, all_badges, new_badges)

        # Optimization: Fetch last log once for time-of-day badges
        time_badges = ['night-owl', 'morning-glory', 'early-bird']
        if any(b not in awarded_slugs for b in time_badges):
            if cache is not None:
                if 'last_log' not in cache:
                    cache['last_log'] = WatchLog.objects.filter(user=user).select_related('episode__season__anime').order_by('-watched_at').first()
                last_log = cache['last_log']
            else:
                last_log = WatchLog.objects.filter(user=user).select_related('episode__season__anime').order_by('-watched_at').first()

            if last_log:
                # 4. Night Owl: Watched an episode between 2 AM and 5 AM.
                if 'night-owl' not in awarded_slugs:
                    if 2 <= last_log.watched_at.hour < 5:
                        self._award(user, 'night-owl', awarded_slugs, all_badges, new_badges)

                # 4.5. Morning Glory: Watched an episode between 6 AM and 9 AM.
                if 'morning-glory' not in awarded_slugs:
                    if 6 <= last_log.watched_at.hour < 9:
                        self._award(user, 'morning-glory', awarded_slugs, all_badges, new_badges)

                # 5. Early Bird: Watched an episode within 1 hour of release.
                if 'early-bird' not in awarded_slugs:
                    diff = last_log.watched_at - last_log.episode.created_at
                    if timedelta(seconds=0) <= diff <= timedelta(hours=1):
                        self._award(user, 'early-bird', awarded_slugs, all_badges, new_badges)

        # 15. Speedster: Watched 3 episodes in 1 hour.
        if 'speedster' not in awarded_slugs:
            last_hour = timezone.now() - timedelta(hours=1)
            count = WatchLog.objects.filter(user=user, watched_at__gte=last_hour).values('episode').distinct().count()
            if count >= 3:
                self._award(user, 'speedster', awarded_slugs, all_badges, new_badges)

class ConsistencyBadgeStrategy(BadgeStrategy):
    def check(self, user, awarded_slugs, all_badges, new_badges, cache=None):
        # 12. Streak Master: Watched anime for 7 consecutive days.
        if 'streak-master' not in awarded_slugs:
            today = timezone.now().date()
            start_date = today - timedelta(days=6)
            start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            days = WatchLog.objects.filter(user=user, watched_at__gte=start_datetime).values('watched_at__date').distinct().count()
            if days >= 7:
                self._award(user, 'streak-master', awarded_slugs, all_badges, new_badges)

        # 13. Daily Viewer: Watched anime for 30 consecutive days.
        if 'daily-viewer' not in awarded_slugs:
            today = timezone.now().date()
            start_date = today - timedelta(days=29)
            start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            days = WatchLog.objects.filter(user=user, watched_at__gte=start_datetime).values('watched_at__date').distinct().count()
            if days >= 30:
                self._award(user, 'daily-viewer', awarded_slugs, all_badges, new_badges)

class AccountBadgeStrategy(BadgeStrategy):
    def check(self, user, awarded_slugs, all_badges, new_badges, cache=None):
        # 2. Supporter: Is Premium.
        if 'supporter' not in awarded_slugs and user.is_premium:
            self._award(user, 'supporter', awarded_slugs, all_badges, new_badges)

        # 3. Veteran: Account created over 1 year ago.
        if 'veteran' not in awarded_slugs:
            if user.date_joined <= timezone.now() - timedelta(days=365):
                self._award(user, 'veteran', awarded_slugs, all_badges, new_badges)

        # 7. Collector: Subscribed to 10 different anime.
        if 'collector' not in awarded_slugs:
            if Subscription.objects.filter(user=user).count() >= 10:
                self._award(user, 'collector', awarded_slugs, all_badges, new_badges)

class ConsumptionBadgeStrategy(BadgeStrategy):
    def check(self, user, awarded_slugs, all_badges, new_badges, cache=None):
        # Optimization: Fetch episode count once
        if 'marathoner' not in awarded_slugs or 'century-club' not in awarded_slugs or 'millennium-club' not in awarded_slugs:
            distinct_episodes = WatchLog.objects.filter(user=user).values('episode').distinct().count()

            # 9. Marathoner: Watched 50 episodes in total.
            if 'marathoner' not in awarded_slugs and distinct_episodes >= 50:
                self._award(user, 'marathoner', awarded_slugs, all_badges, new_badges)

            # 27. Century Club: Watched 100 episodes.
            if 'century-club' not in awarded_slugs and distinct_episodes >= 100:
                self._award(user, 'century-club', awarded_slugs, all_badges, new_badges)

            # 33. Millennium Club: Watched 1000 distinct episodes.
            if 'millennium-club' not in awarded_slugs and distinct_episodes >= 1000:
                self._award(user, 'millennium-club', awarded_slugs, all_badges, new_badges)

        # 11. Loyal Fan: Watched 10 episodes of the same anime.
        if 'loyal-fan' not in awarded_slugs:
            if cache is not None:
                if 'last_log' not in cache:
                    cache['last_log'] = WatchLog.objects.filter(user=user).select_related('episode__season__anime').order_by('-watched_at').first()
                last_log = cache['last_log']
            else:
                last_log = WatchLog.objects.filter(user=user).select_related('episode__season__anime').order_by('-watched_at').first()
            if last_log:
                anime = last_log.episode.season.anime
                count = WatchLog.objects.filter(user=user, episode__season__anime=anime).values('episode').distinct().count()
                if count >= 10:
                    self._award(user, 'loyal-fan', awarded_slugs, all_badges, new_badges)

        # 20. Pilot Connoisseur: Watched the first episode of 5 different anime series.
        if 'pilot-connoisseur' not in awarded_slugs:
            count = WatchLog.objects.filter(user=user, episode__number=1).values('episode__season__anime').distinct().count()
            if count >= 5:
                self._award(user, 'pilot-connoisseur', awarded_slugs, all_badges, new_badges)

        # Optimization: Fetch type counts once
        type_badges = ['movie-buff', 'tv-addict', 'ova-enthusiast']
        if any(b not in awarded_slugs for b in type_badges):
            type_counts_qs = Anime.objects.filter(
                seasons__episodes__watch_logs__user=user
            ).values('type').annotate(count=Count('id', distinct=True))

            type_counts = {item['type']: item['count'] for item in type_counts_qs}

            # 21. Movie Buff: Watched 5 different anime movies.
            if 'movie-buff' not in awarded_slugs:
                if type_counts.get('Movie', 0) >= 5:
                    self._award(user, 'movie-buff', awarded_slugs, all_badges, new_badges)

            # 28. TV Addict: Watched 10 different TV Series.
            if 'tv-addict' not in awarded_slugs:
                if type_counts.get('TV', 0) >= 10:
                    self._award(user, 'tv-addict', awarded_slugs, all_badges, new_badges)

            # 29. OVA Enthusiast: Watched 5 different OVAs.
            if 'ova-enthusiast' not in awarded_slugs:
                if type_counts.get('OVA', 0) >= 5:
                    self._award(user, 'ova-enthusiast', awarded_slugs, all_badges, new_badges)

class CompletionBadgeStrategy(BadgeStrategy):
    def check(self, user, awarded_slugs, all_badges, new_badges, cache=None):
        # Optimization: Fetch last log once for both season-completist and super-fan
        if 'season-completist' not in awarded_slugs or 'super-fan' not in awarded_slugs:
            if cache is not None:
                if 'last_log' not in cache:
                    cache['last_log'] = WatchLog.objects.filter(user=user).select_related('episode__season__anime').order_by('-watched_at').first()
                last_log = cache['last_log']
            else:
                last_log = WatchLog.objects.filter(user=user).select_related('episode__season__anime').order_by('-watched_at').first()
            if last_log:
                season = last_log.episode.season
                anime = season.anime

                # 8. Season Completist: Completed an entire season.
                if 'season-completist' not in awarded_slugs:
                    total_season = season.episodes.count()
                    if total_season > 0:
                        watched_season = WatchLog.objects.filter(user=user, episode__season=season).values('episode').distinct().count()
                        if watched_season >= total_season:
                            self._award(user, 'season-completist', awarded_slugs, all_badges, new_badges)

                # 23. Super Fan: Completed all episodes of an anime series.
                if 'super-fan' not in awarded_slugs:
                    total_anime = Episode.objects.filter(season__anime=anime).count()
                    if total_anime > 0:
                        watched_anime = WatchLog.objects.filter(user=user, episode__season__anime=anime).values('episode').distinct().count()
                        if watched_anime >= total_anime:
                            self._award(user, 'super-fan', awarded_slugs, all_badges, new_badges)

        # 26. Otaku: Completed 5 different anime series.
        if 'otaku' not in awarded_slugs:
            if cache is not None:
                if 'anime_ids' not in cache:
                    cache['anime_ids'] = list(WatchLog.objects.filter(user=user).values_list('episode__season__anime_id', flat=True).distinct())
                watched_anime_ids = cache['anime_ids']
            else:
                watched_anime_ids = list(WatchLog.objects.filter(user=user).values_list('episode__season__anime_id', flat=True).distinct())
            if watched_anime_ids:
                total_episodes_qs = Episode.objects.filter(season__anime_id__in=watched_anime_ids).values('season__anime_id').annotate(total=Count('id'))
                total_map = {i['season__anime_id']: i['total'] for i in total_episodes_qs}

                user_watched_qs = WatchLog.objects.filter(user=user, episode__season__anime_id__in=watched_anime_ids).values('episode__season__anime_id').annotate(watched=Count('episode', distinct=True))
                watched_map = {i['episode__season__anime_id']: i['watched'] for i in user_watched_qs}

                completed = 0
                for aid in watched_anime_ids:
                    if total_map.get(aid, 0) > 0 and watched_map.get(aid, 0) >= total_map.get(aid, 0):
                        completed += 1

                if completed >= 5:
                    self._award(user, 'otaku', awarded_slugs, all_badges, new_badges)

class GenreBadgeStrategy(BadgeStrategy):
    def check(self, user, awarded_slugs, all_badges, new_badges, cache=None):
        anime_ids = None

        def get_anime_ids():
            nonlocal anime_ids
            if anime_ids is not None:
                return anime_ids
            if cache is not None:
                if 'anime_ids' not in cache:
                    cache['anime_ids'] = list(WatchLog.objects.filter(user=user).values_list('episode__season__anime_id', flat=True).distinct())
                anime_ids = cache['anime_ids']
            else:
                anime_ids = list(WatchLog.objects.filter(user=user).values_list('episode__season__anime_id', flat=True).distinct())
            return anime_ids

        # 10. Genre Explorer: Watched anime from 5 different genres.
        if 'genre-explorer' not in awarded_slugs:
            ids = get_anime_ids()
            count = Anime.objects.filter(id__in=ids).values('genres__id').distinct().count()
            if count >= 5:
                self._award(user, 'genre-explorer', awarded_slugs, all_badges, new_badges)

        # 14. Genre Master: Watched 10 different anime from the same genre.
        if 'genre-master' not in awarded_slugs:
            ids = get_anime_ids()
            if ids:
                qs = Genre.objects.filter(animes__id__in=ids).annotate(
                    user_anime_count=Count('animes', filter=Q(animes__id__in=ids))
                )
                if qs.filter(user_anime_count__gte=10).exists():
                    self._award(user, 'genre-master', awarded_slugs, all_badges, new_badges)

        # 19. Genre Savant: Watched 50 episodes of a single genre.
        if 'genre-savant' not in awarded_slugs:
            episode_ids = WatchLog.objects.filter(user=user).values_list('episode_id', flat=True).distinct()
            if episode_ids:
                qs = Genre.objects.filter(animes__seasons__episodes__id__in=episode_ids).annotate(
                    user_episode_count=Count('animes__seasons__episodes', filter=Q(animes__seasons__episodes__id__in=episode_ids), distinct=True)
                )
                if qs.filter(user_episode_count__gte=50).exists():
                    self._award(user, 'genre-savant', awarded_slugs, all_badges, new_badges)

class SpecificGenreBadgeStrategy(BadgeStrategy):
    def check(self, user, awarded_slugs, all_badges, new_badges, cache=None):
        # Optimization: Fetch all genre counts once to handle case-insensitivity
        if 'nightmare' not in awarded_slugs or 'comedy-gold' not in awarded_slugs:
            genre_counts_qs = Anime.objects.filter(
                seasons__episodes__watch_logs__user=user
            ).values('genres__name').annotate(count=Count('id', distinct=True))

            # Map genre name lowercased
            genre_counts = {}
            for item in genre_counts_qs:
                name = item['genres__name']
                if name:
                    name_lower = name.lower()
                    genre_counts[name_lower] = genre_counts.get(name_lower, 0) + item['count']

            # 30. Nightmare: Watched 5 Horror anime.
            if 'nightmare' not in awarded_slugs:
                if genre_counts.get('horror', 0) >= 5:
                    self._award(user, 'nightmare', awarded_slugs, all_badges, new_badges)

            # 31. Comedy Gold: Watched 5 Comedy anime.
            if 'comedy-gold' not in awarded_slugs:
                if genre_counts.get('comedy', 0) >= 5:
                    self._award(user, 'comedy-gold', awarded_slugs, all_badges, new_badges)

class CommunityBadgeStrategy(BadgeStrategy):
    def check(self, user, awarded_slugs, all_badges, new_badges, cache=None):
        # 16. Party Host: Hosted 5 Watch Parties.
        if 'party-host' not in awarded_slugs:
            if Room.objects.filter(host=user).count() >= 5:
                self._award(user, 'party-host', awarded_slugs, all_badges, new_badges)

        # 22. Trendsetter: Hosted a Watch Party with 5 concurrent viewers.
        if 'trendsetter' not in awarded_slugs:
            if Room.objects.filter(host=user, max_participants__gte=5).exists():
                self._award(user, 'trendsetter', awarded_slugs, all_badges, new_badges)

        # 18. Content Creator: Uploaded 5 videos.
        if 'content-creator' not in awarded_slugs:
            if VideoFile.objects.filter(uploader=user).count() >= 5:
                self._award(user, 'content-creator', awarded_slugs, all_badges, new_badges)

class ChatBadgeStrategy(BadgeStrategy):
    def check(self, user, awarded_slugs, all_badges, new_badges, cache=None):
        # 5. Commentator: Posted 50 chat messages.
        if 'commentator' not in awarded_slugs:
            if ChatMessage.objects.filter(user=user).count() >= 50:
                self._award(user, 'commentator', awarded_slugs, all_badges, new_badges)

        # 6. Social Butterfly: Participated in 5 different chat rooms.
        if 'social-butterfly' not in awarded_slugs:
            if ChatMessage.objects.filter(user=user).values('room_name').distinct().count() >= 5:
                self._award(user, 'social-butterfly', awarded_slugs, all_badges, new_badges)

        # 17. Party Animal: Participated in 5 different Watch Parties.
        if 'party-animal' not in awarded_slugs:
            count = ChatMessage.objects.filter(user=user, room_name__startswith='party_').values('room_name').distinct().count()
            if count >= 5:
                self._award(user, 'party-animal', awarded_slugs, all_badges, new_badges)


# Strategy Lists
GENERAL_BADGE_STRATEGIES = [
    ReviewBadgeStrategy(),
    WatchTimeBadgeStrategy(),
    ConsistencyBadgeStrategy(),
    AccountBadgeStrategy(),
    ConsumptionBadgeStrategy(),
    CompletionBadgeStrategy(),
    GenreBadgeStrategy(),
    SpecificGenreBadgeStrategy(),
    CommunityBadgeStrategy(),
]

CHAT_BADGE_STRATEGIES = [
    ChatBadgeStrategy(),
]
