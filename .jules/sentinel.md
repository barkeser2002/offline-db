## YYYY-MM-DD - Sentinel Journal
**Vulnerability:** RoomViewSet lacks authorization checks for update/delete. Any authenticated user can modify or delete ANY room by sending PUT/DELETE requests to `/api/watch-parties/{uuid}/`.
**Learning:** ModelViewSet provides `update` and `destroy` actions by default. Without custom permissions (like `IsHostOrReadOnly`) or overriding `get_queryset()` to filter by user for unsafe methods, IDOR vulnerabilities are introduced.
**Prevention:** Override `perform_update` and `perform_destroy` to check `instance.host == self.request.user`, or use a custom permission class, or filter `get_queryset()`.

## 2024-05-24 - [Exposed Video Encryption Key]
**Vulnerability:** The `encryption_key` field was included in the `VideoFileSerializer`, exposing the HLS video encryption key in plain text via the API.
**Learning:** Django Rest Framework's `ModelSerializer` will expose sensitive fields if they are explicitly listed in the `fields` array of the `Meta` class, bypassing the intended secure serving mechanisms (like `KeyServeView`).
**Prevention:** Never include sensitive fields (passwords, encryption keys, tokens) in standard API serializers unless explicitly required and protected. Serve them securely via dedicated endpoints with appropriate authentication and authorization checks.

## 2024-05-24 - [Missing Authentication on Custom ViewSet Actions]
**Vulnerability:** A custom DRF ViewSet action (`@action(detail=False, methods=['get'])`) intended only for authenticated users allowed unauthenticated access because the class-level permissions were `[IsAuthenticatedOrReadOnly]`. This lead to a `ValueError` (and 500 error) when the code incorrectly assumed `request.user` was a valid user instance instead of `AnonymousUser`.
**Learning:** Class-level `permission_classes` apply to all custom actions unless overridden. Using `IsAuthenticatedOrReadOnly` at the class level means custom actions will inherit the "allow read-only for anonymous" behavior, which is dangerous if the action accesses user-specific data.
**Prevention:** Always explicitly set `permission_classes=[IsAuthenticated]` on custom `@action` endpoints that require authentication, overriding the class-level defaults when necessary.
