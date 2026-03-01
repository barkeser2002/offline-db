## 2024-10-27 - Badge System Optimization
**Learning:** The badge system uses multiple independent queries to filter `WatchLog` for different time windows.
**Action:** Optimize `WatchTimeBadgeStrategy` by combining overlapping queries.

## 2024-10-27 - Badge System CompletionBadgeStrategy Optimization
**Learning:** `CompletionBadgeStrategy` originally fetched the most recent `WatchLog` in a completely separate query with joins (`select_related('episode__season__anime')`) for the `super-fan` badge, even if it had already just fetched exactly the same log with a similar query (`select_related('episode__season')`) for the `season-completist` badge.
**Action:** Optimize `CompletionBadgeStrategy` to fetch the most recent log once, eagerly loading `episode__season__anime`, and reuse this data for evaluating both `season-completist` and `super-fan` badges. This reduces redundant database hits.
