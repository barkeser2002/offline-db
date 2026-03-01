## 2024-10-27 - Badge System Optimization
**Learning:** The badge system uses multiple independent queries to filter `WatchLog` for different time windows.
**Action:** Optimize `WatchTimeBadgeStrategy` by combining overlapping queries.

## 2024-10-27 - Badge System CompletionBadgeStrategy Optimization
**Learning:** `CompletionBadgeStrategy` originally fetched the most recent `WatchLog` in a completely separate query with joins (`select_related('episode__season__anime')`) for the `super-fan` badge, even if it had already just fetched exactly the same log with a similar query (`select_related('episode__season')`) for the `season-completist` badge.
**Action:** Optimize `CompletionBadgeStrategy` to fetch the most recent log once, eagerly loading `episode__season__anime`, and reuse this data for evaluating both `season-completist` and `super-fan` badges. This reduces redundant database hits.

## 2025-03-01 - Global Badge System Optimization (Cache Context)
**Learning:** We had individual strategies successfully optimized internally, but different strategies shared the exact same queries (e.g. `WatchLog.objects.filter(user=user).select_related('episode__season__anime').order_by('-watched_at').first()`). Due to isolation in strategy pattern, redundant database calls were made.
**Action:** Introduced a `cache` argument into the base `BadgeStrategy.check()` signature and propagated a `cache` dictionary instance from the service layer, enabling strategies to store and retrieve results of expensive or commonly repeated queries (e.g., `last_log`, `anime_ids`) across boundaries.
