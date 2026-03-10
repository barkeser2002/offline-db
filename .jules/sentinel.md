## YYYY-MM-DD - Sentinel Journal
**Vulnerability:** RoomViewSet lacks authorization checks for update/delete. Any authenticated user can modify or delete ANY room by sending PUT/DELETE requests to `/api/watch-parties/{uuid}/`.
**Learning:** ModelViewSet provides `update` and `destroy` actions by default. Without custom permissions (like `IsHostOrReadOnly`) or overriding `get_queryset()` to filter by user for unsafe methods, IDOR vulnerabilities are introduced.
**Prevention:** Override `perform_update` and `perform_destroy` to check `instance.host == self.request.user`, or use a custom permission class, or filter `get_queryset()`.

## 2024-05-24 - [Exposed Video Encryption Key]
**Vulnerability:** The `encryption_key` field was included in the `VideoFileSerializer`, exposing the HLS video encryption key in plain text via the API.
**Learning:** Django Rest Framework's `ModelSerializer` will expose sensitive fields if they are explicitly listed in the `fields` array of the `Meta` class, bypassing the intended secure serving mechanisms (like `KeyServeView`).
**Prevention:** Never include sensitive fields (passwords, encryption keys, tokens) in standard API serializers unless explicitly required and protected. Serve them securely via dedicated endpoints with appropriate authentication and authorization checks.

## 2025-03-10 - [Path Traversal in Storage Backend]
**Vulnerability:** The `LocalStorage` backend in `core/storage.py` suffered from a Path Traversal vulnerability (CWE-22) because `os.path.join()` was used to directly append a user-provided `remote_path` to `self.base_path` without bounds checking. An attacker could supply absolute paths (like `/etc/passwd`) or relative traversal sequences (`../../../../etc/passwd`) to overwrite or delete sensitive host machine files.
**Learning:** `os.path.join` ignores the base path if the subsequent path string starts with a `/`. Even if it doesn't, relative `../` components allow escaping the intended directory.
**Prevention:** Always resolve the absolute path (`os.path.abspath`) and strictly verify that it resides within the intended directory using `startswith(base_path + os.sep)` or `os.path.commonpath([base_path, full_path]) == base_path` to prevent both standard traversal and sibling directory bypassing (e.g. `../media_secrets/`).
