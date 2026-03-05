## 2024-10-27 - Badge System Optimization
**Learning:** The badge system uses multiple independent queries to filter `WatchLog` for different time windows.
**Action:** Optimize `WatchTimeBadgeStrategy` by combining overlapping queries.

## 2024-10-27 - Badge System CompletionBadgeStrategy Optimization
**Learning:** `CompletionBadgeStrategy` originally fetched the most recent `WatchLog` in a completely separate query with joins (`select_related('episode__season__anime')`) for the `super-fan` badge, even if it had already just fetched exactly the same log with a similar query (`select_related('episode__season')`) for the `season-completist` badge.
**Action:** Optimize `CompletionBadgeStrategy` to fetch the most recent log once, eagerly loading `episode__season__anime`, and reuse this data for evaluating both `season-completist` and `super-fan` badges. This reduces redundant database hits.

## 2025-03-01 - Global Badge System Optimization (Cache Context)
**Learning:** We had individual strategies successfully optimized internally, but different strategies shared the exact same queries (e.g. `WatchLog.objects.filter(user=user).select_related('episode__season__anime').order_by('-watched_at').first()`). Due to isolation in strategy pattern, redundant database calls were made.
**Action:** Introduced a `cache` argument into the base `BadgeStrategy.check()` signature and propagated a `cache` dictionary instance from the service layer, enabling strategies to store and retrieve results of expensive or commonly repeated queries (e.g., `last_log`, `anime_ids`) across boundaries.

## 2025-03-01 - Global Global Badge System Optimization (Avoid Heavy WatchLog Joins)
**Learning:** Multiple badge strategies (`ConsumptionBadgeStrategy`, `SpecificGenreBadgeStrategy`, `GenreBadgeStrategy`) were performing expensive `JOIN`s from `Anime` down to `WatchLog` (e.g., `seasons__episodes__watch_logs__user=user`) multiple times per evaluation cycle. This was particularly heavy given `WatchLog` is the largest table in the database.
**Action:** Changed the strategies to reuse the locally cached list of `anime_ids` and `episode_ids` and replaced the heavy 4-table join with a simple `id__in=anime_ids` and `id__in=episode_ids` check directly against the `Anime` and `Genre` queries.

## 2025-03-03 - Badge System Optimization (Eliminate Redundant check_badges calls)
**Learning:** `check_badges(user)` was being called manually in DRF viewsets (e.g., `ReviewViewSet.perform_create`, `WatchLogViewSet.perform_create`) even though `post_save` signals for `Review` and `WatchLog` were already configured to trigger `check_badges` automatically. This double-fired the entire badge evaluation logic for common user actions.
**Action:** Removed redundant `check_badges(user)` calls from views that are already covered by Django signals, halving the database overhead on `WatchLog` and `Review` creations.

## 2025-03-03 - Badge System Optimization (Cache All Badges)
**Learning:** Even with strategies optimized internally, `Badge.objects.all()` was being queried from the database every single time `check_badges` or `check_chat_badges` was executed. Because badges change very infrequently, this is a prime candidate for application-level caching.
**Action:** Introduced Django's `cache` mechanism to store the `all_badges` dictionary for 1 hour, retrieving it from memory instead of the database, saving a redundant SQL lookup on every badge evaluation trigger.

## 2025-03-03 - Template Tag Query Optimization
**Learning:** Template tags like `get_ad` that are used in the main application layout (`base.html`) and contain database queries (e.g., fetching an `AdSlot`) cause a hidden N+1-like issue by triggering an independent query on *every single page load* for non-premium users.
**Action:** Cached the output of the template tag via Django's `core.cache` and added signal hooks to invalidate the cache only when the underlying `AdSlot` model is saved or deleted.

## 2025-03-05 - Badge System Query Count Optimization
**Learning:** `CommunityBadgeStrategy`, `ChatBadgeStrategy`, and `ConsistencyBadgeStrategy` were issuing multiple independent `.count()` and `.exists()` queries against the database to evaluate different thresholds of the same data (e.g., checking if a user hosted 5 rooms, then immediately checking if they hosted a room with 5 participants).
**Action:** Replaced separate DB aggregation queries with a single query that fetches the relevant distinct rows into the shared `cache` dictionary (e.g., `Room.objects.filter(host=user).values('max_participants')`). The `.count()` and `.exists()` logic is then evaluated in memory using Python's `len()`, `any()`, and `sum()`, drastically reducing the total database queries per badge evaluation cycle.
