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

## 2025-03-07 - Badge System Strategy Caching
**Learning:** Even though we had implemented caching inside `users/badge_system.py` using a shared `cache` dict, it was partially unused in strategies that needed a `.distinct().count()`. Querying `.distinct().count()` skips memory and always hits the database.
**Action:** Used `len(cache['episode_ids'])` where `episode_ids` was already stored as a flat list, saving a whole `.distinct().count()` aggregation query from `ConsumptionBadgeStrategy`. This demonstrates that when you already have a distinct list of IDs cached, doing `len()` in python is much faster and saves an extra DB query.

## 2025-03-09 - Badge System Pilot Connoisseur Optimization
**Learning:** `pilot-connoisseur` badge check was performing an expensive `JOIN` traversing `WatchLog`, `Episode`, `Season` and `Anime` to count distinct anime series. And because `.distinct().count()` skips memory and hits the DB, it was issuing a new heavy aggregation query.
**Action:** Leveraged the shared `cache['episode_ids']` and replaced the expensive `WatchLog` join with an `id__in=episode_ids` check directly on the `Episode` model. Additionally, fetched the results as a flat list and evaluated uniqueness in memory using Python's `len(set(...))` to prevent the `.distinct().count()` database query overhead.

## 2025-03-09 - Badge System Genre Optimization
**Learning:** `GenreBadgeStrategy` queries for `genre-explorer`, `genre-master`, and `genre-savant` were extremely inefficient. They relied on `.distinct().count()`, reverse relationship `.annotate(Count())`, and complex 4-table `.exists()` lookups which bypassed our previously implemented memory caching and heavily taxed the database with redundant JOIN operations on the largest tables (`WatchLog` and `Episode`).
**Action:** Replaced these heavy database queries with simpler `values_list(..., flat=True)` queries to fetch raw IDs directly related to the user's cached `anime_ids` and `episode_ids`. We then process these IDs in-memory using pure Python (e.g., `len(set())` and `collections.Counter()`). This dramatically reduces database CPU load and memory usage by offloading computation to the Python runtime, and drops total queries per user evaluation cycle.

## 2024-10-28 - Badge System distinct().count() Optimization
**Learning:** `CompletionBadgeStrategy` (`season-completist`, `super-fan`) and `ConsumptionBadgeStrategy` (`loyal-fan`) were issuing `.distinct().count()` aggregation queries with JOINs on `WatchLog` to evaluate watched episodes for specific seasons and animes. Since `.distinct().count()` skips memory and always hits the database, these queries were adding unnecessary database load.
**Action:** Refactored these strategies to utilize the shared `cache['episode_ids']`. By fetching the target `Episode` IDs (e.g., for a season or anime) as a flat list and intersecting them with the cached `episode_ids` set in memory using Python (`len(target_ep_ids.intersection(user_ep_ids))`), we eliminate the heavy `WatchLog` joins and redundant aggregation queries, significantly reducing database load per evaluation cycle.

## 2025-03-09 - WatchTimeBadgeStrategy count optimization
**Learning:** `WatchTimeBadgeStrategy` checks for `binge-watcher`, `marathon-runner`, `weekend-warrior`, and `speedster` badges were issuing `.distinct().count()` aggregation queries with JOINs on `WatchLog`. Since `.distinct().count()` skips memory and always hits the database, these queries were adding unnecessary database load.
**Action:** Replaced these heavy database queries with `len(set(WatchLog.objects.filter(...).values_list('episode_id', flat=True)))`. This pattern avoids the expensive database-level `.distinct().count()` aggregation by executing a simpler select and evaluating uniqueness and size in Python memory, reducing database load per evaluation cycle.

## 2026-03-20 - Optimized Encoder/Fansub Wallet Distribution
**Learning:** The revenue distribution logic in `billing/tasks.py` performed individual `get_or_create` and `save` operations for `Wallet` objects inside loops for encoders and fansub group owners. This created an N+1 query bottleneck that scaled with the number of unique payment recipients.
**Action:** Refactored the task to consolidate all earnings by `user_id` in memory. Implemented bulk database operations using `Wallet.objects.bulk_create` (with `ignore_conflicts=True`) for missing wallets and `Wallet.objects.bulk_update` for updating all balances in a single transaction. This reduces database overhead from O(N) to O(1) queries.
## 2026-03-05 - Bolt: Convert genre_savant episode_ids to subquery
**Learning:** Fetching a large dataset of IDs into a Python list (`list(values_list("episode_id", flat=True))`) to perform in-memory aggregations or subquery lookups creates massive SQL queries and high memory overhead, especially for complex relationships like genre counts.
**Action:** Replaced the in-memory list with an un-evaluated Django QuerySet subquery (`episode_qs = WatchLog.objects.filter(user=user).values("episode_id")`), and utilized `.annotate(count=Count("id", distinct=True))` to evaluate genre distributions purely at the database level without transferring records.

## 2025-03-10 - [Optimize genre-savant badge strategy]
**Learning:** `WatchLog.objects.filter(user=user).values('episode_id')` would pull episode ids into memory which were then passed to `.filter(id__in=episode_qs)`. This resulted in excessive database fetching and memory use.
**Action:** Substituted the two-step evaluation process into a single optimized query string that handles filtering, related joins, and aggregations purely at the database level by traversing models via double-underscores (`episode__season__anime__genres__id`).

## 2026-03-05 - NotificationViewSet Performance Improvement
**Learning:** To significantly improve performance of DRF ViewSets like `NotificationViewSet` that frequently filter and order by specific fields (e.g., `filter(user=request.user).order_by('-created_at')` and `filter(is_read=False)`), add composite database indexes to the Django model's `Meta` class (e.g., `models.Index(fields=['user', 'is_read'])` and `models.Index(fields=['user', '-created_at'])`).
**Action:** Added composite indexes `['user', 'is_read']` and `['user', '-created_at']` to the `Notification` model's `Meta` class in `users/models.py` and created the corresponding database migrations.

## 2024-03-13 - [Add composite indexes to WatchLog and Subscription models]
**Learning:** To significantly improve performance of querying large tables like `WatchLog` and `Subscription` which are frequently filtered by combinations of `user` and `watched_at` or `user` and `anime`, composite database indexes should be added.
**Action:** Added `['user', 'watched_at']` to `WatchLog` and `['user', 'anime']` to `Subscription` in `users/models.py` and `content/models.py` respectively, and generated migrations.

## 2026-03-13 - [Add index to Room is_active]
**Learning:** The `Room` model is frequently filtered by `is_active=True` across the application. Adding an index to this boolean field can improve query performance.
**Action:** Added `models.Index(fields=['is_active'])` to the `Room` model in `apps/watchparty/models.py` and generated the corresponding migration.

## 2025-04-13 - [Optimize Otaku Badge logic with single aggregation query]
**Learning:** The 'otaku' badge strategy was previously using two separate database queries and a Python-side loop to compare total vs. watched episodes per anime series. This pattern increases database round-trips and memory overhead as the number of anime series grows.
**Action:** Consolidated the logic into a single database-level query using Django's `annotate()` with conditional `Count()` and `F()` expressions. This allows the database to perform the completion check directly, reducing the result set and improving execution speed.

## 2026-04-19 - Badge System check_badges N+1 Optimization
**Learning:** In `users/services.py`, `check_badges()` iterated over `GENERAL_BADGE_STRATEGIES` and `CHAT_BADGE_STRATEGIES`, triggering multiple database queries (like fetching `episode_ids` and `anime_ids`) inside the loop from each strategy's `check()` method.
**Action:** Pre-populated the `strategy_cache` dictionary with common bulk datasets before executing the strategy loop, eliminating the N+1 query issue and centralizing database queries outside the evaluation logic.
