## YYYY-MM-DD - Sentinel Journal
**Vulnerability:** RoomViewSet lacks authorization checks for update/delete. Any authenticated user can modify or delete ANY room by sending PUT/DELETE requests to `/api/watch-parties/{uuid}/`.
**Learning:** ModelViewSet provides `update` and `destroy` actions by default. Without custom permissions (like `IsHostOrReadOnly`) or overriding `get_queryset()` to filter by user for unsafe methods, IDOR vulnerabilities are introduced.
**Prevention:** Override `perform_update` and `perform_destroy` to check `instance.host == self.request.user`, or use a custom permission class, or filter `get_queryset()`.
