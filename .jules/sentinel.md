## YYYY-MM-DD - Sentinel Journal
**Vulnerability:** RoomViewSet lacks authorization checks for update/delete. Any authenticated user can modify or delete ANY room by sending PUT/DELETE requests to `/api/watch-parties/{uuid}/`.
**Learning:** ModelViewSet provides `update` and `destroy` actions by default. Without custom permissions (like `IsHostOrReadOnly`) or overriding `get_queryset()` to filter by user for unsafe methods, IDOR vulnerabilities are introduced.
**Prevention:** Override `perform_update` and `perform_destroy` to check `instance.host == self.request.user`, or use a custom permission class, or filter `get_queryset()`.

## 2024-05-24 - [Exposed Video Encryption Key]
**Vulnerability:** The `encryption_key` field was included in the `VideoFileSerializer`, exposing the HLS video encryption key in plain text via the API.
**Learning:** Django Rest Framework's `ModelSerializer` will expose sensitive fields if they are explicitly listed in the `fields` array of the `Meta` class, bypassing the intended secure serving mechanisms (like `KeyServeView`).
**Prevention:** Never include sensitive fields (passwords, encryption keys, tokens) in standard API serializers unless explicitly required and protected. Serve them securely via dedicated endpoints with appropriate authentication and authorization checks.

## 2024-05-25 - [WatchParty WebSocket Auth & Connection Rejection]
**Vulnerability:** The `WatchPartyConsumer` incorrectly accepted connections before checking authentication, allowing unauthenticated users to listen to private watch party WebSockets. Additionally, non-existent room connections were rejected by calling `await self.close()` before `await self.accept()`, causing an ASGI protocol violation and test failures due to `ValueError` in `URLRouter`.
**Learning:** In Django Channels, attempting to gracefully `close()` a WebSocket connection before accepting it violates the ASGI protocol. Furthermore, `URLRouter` enforces regex patterns strictly; tests failing due to mismatched parameters (e.g., passing "party_nonexistentuuid" when `[0-9a-f-]+` is expected) will never reach the consumer logic.
**Prevention:** Use `raise DenyConnection()` from `channels.exceptions` to properly reject unauthenticated or invalid WebSocket connections during the `connect` phase. Ensure test URLs match routing regex constraints.
