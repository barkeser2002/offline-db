## YYYY-MM-DD - Sentinel Journal
**Vulnerability:** RoomViewSet lacks authorization checks for update/delete. Any authenticated user can modify or delete ANY room by sending PUT/DELETE requests to `/api/watch-parties/{uuid}/`.
**Learning:** ModelViewSet provides `update` and `destroy` actions by default. Without custom permissions (like `IsHostOrReadOnly`) or overriding `get_queryset()` to filter by user for unsafe methods, IDOR vulnerabilities are introduced.
**Prevention:** Override `perform_update` and `perform_destroy` to check `instance.host == self.request.user`, or use a custom permission class, or filter `get_queryset()`.

## 2024-05-24 - [Exposed Video Encryption Key]
**Vulnerability:** The `encryption_key` field was included in the `VideoFileSerializer`, exposing the HLS video encryption key in plain text via the API.
**Learning:** Django Rest Framework's `ModelSerializer` will expose sensitive fields if they are explicitly listed in the `fields` array of the `Meta` class, bypassing the intended secure serving mechanisms (like `KeyServeView`).
**Prevention:** Never include sensitive fields (passwords, encryption keys, tokens) in standard API serializers unless explicitly required and protected. Serve them securely via dedicated endpoints with appropriate authentication and authorization checks.

## 2024-05-24 - [IP Spoofing / Rate Limit Bypass]
**Vulnerability:** Using `request.META.get('REMOTE_ADDR')` for rate limiting and logging when the application is behind a reverse proxy (like Nginx) limits the proxy's IP instead of the client's. This allows a single attacker to exhaust the limit for all legitimate users or spoof their IP for logging.
**Learning:** `REMOTE_ADDR` reflects the immediate previous hop. In a proxied setup, the actual client IP must be extracted from the `HTTP_X_FORWARDED_FOR` header.
**Prevention:** Always use a utility function like `get_client_ip(request)` that securely extracts the first IP from `HTTP_X_FORWARDED_FOR`, falling back to `REMOTE_ADDR` if not present.
