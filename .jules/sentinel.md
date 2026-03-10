## YYYY-MM-DD - Sentinel Journal
**Vulnerability:** RoomViewSet lacks authorization checks for update/delete. Any authenticated user can modify or delete ANY room by sending PUT/DELETE requests to `/api/watch-parties/{uuid}/`.
**Learning:** ModelViewSet provides `update` and `destroy` actions by default. Without custom permissions (like `IsHostOrReadOnly`) or overriding `get_queryset()` to filter by user for unsafe methods, IDOR vulnerabilities are introduced.
**Prevention:** Override `perform_update` and `perform_destroy` to check `instance.host == self.request.user`, or use a custom permission class, or filter `get_queryset()`.

## 2024-05-24 - [Exposed Video Encryption Key]
**Vulnerability:** The `encryption_key` field was included in the `VideoFileSerializer`, exposing the HLS video encryption key in plain text via the API.
**Learning:** Django Rest Framework's `ModelSerializer` will expose sensitive fields if they are explicitly listed in the `fields` array of the `Meta` class, bypassing the intended secure serving mechanisms (like `KeyServeView`).
**Prevention:** Never include sensitive fields (passwords, encryption keys, tokens) in standard API serializers unless explicitly required and protected. Serve them securely via dedicated endpoints with appropriate authentication and authorization checks.

## $(date +%Y-%m-%d) - [Insecure Direct Object Modification in Audit Logs]
**Vulnerability:** `NotificationViewSet` and `WatchLogViewSet` inherited from `viewsets.ModelViewSet`, which exposes all CRUD operations by default (Create, Retrieve, Update, Delete, List). While their `get_queryset()` methods filtered by `request.user` (preventing IDOR for *viewing* or *modifying* other users' data), users could still arbitrarily modify (PUT/PATCH) or delete (DELETE) their own `WatchLog`s or `Notification`s via the API, which should be immutable or handled via specific actions (e.g., mark as read).
**Learning:** Using `viewsets.ModelViewSet` exposes all standard CRUD routes. If the business logic dictates that a record is an immutable audit log (like a watch history entry) or should only be interacted with via specific actions, `ModelViewSet` exposes unintended state manipulation vulnerabilities, even if the queryset restricts access to the user's own objects.
**Prevention:** For read-only endpoints, use `viewsets.ReadOnlyModelViewSet`. For endpoints with specific write actions (like creating a log or viewing a list), explicitly inherit from `viewsets.GenericViewSet` and only include the required mixins (e.g., `mixins.CreateModelMixin`, `mixins.ListModelMixin`, `mixins.RetrieveModelMixin`), intentionally omitting `UpdateModelMixin` and `DestroyModelMixin`.
