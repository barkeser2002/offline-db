## 2024-10-27 - Badge System Optimization
**Learning:** The badge system uses multiple independent queries to filter `WatchLog` for different time windows.
**Action:** Optimize `WatchTimeBadgeStrategy` by combining overlapping queries.
