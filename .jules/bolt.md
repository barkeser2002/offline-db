# Bolt's Journal

This journal tracks critical performance learnings, failed experiments, and architectural insights.

## [YYYY-MM-DD] - [Initial Setup]
**Learning:** Initial journal creation.
**Action:** Start documenting performance findings.

## 2024-05-22 - [N+1 on Home Page]
**Learning:** Home page performance was bottlenecked by N+1 queries for genres on anime lists.
**Action:** Always use `prefetch_related` when serializing related fields in list views.
