## YYYY-MM-DD - Sentinel Journal
**Vulnerability:** RoomViewSet lacks authorization checks for update/delete. Any authenticated user can modify or delete ANY room by sending PUT/DELETE requests to `/api/watch-parties/{uuid}/`.
**Learning:** ModelViewSet provides `update` and `destroy` actions by default. Without custom permissions (like `IsHostOrReadOnly`) or overriding `get_queryset()` to filter by user for unsafe methods, IDOR vulnerabilities are introduced.
**Prevention:** Override `perform_update` and `perform_destroy` to check `instance.host == self.request.user`, or use a custom permission class, or filter `get_queryset()`.

## 2024-05-24 - [Exposed Video Encryption Key]
**Vulnerability:** The `encryption_key` field was included in the `VideoFileSerializer`, exposing the HLS video encryption key in plain text via the API.
**Learning:** Django Rest Framework's `ModelSerializer` will expose sensitive fields if they are explicitly listed in the `fields` array of the `Meta` class, bypassing the intended secure serving mechanisms (like `KeyServeView`).
**Prevention:** Never include sensitive fields (passwords, encryption keys, tokens) in standard API serializers unless explicitly required and protected. Serve them securely via dedicated endpoints with appropriate authentication and authorization checks.

## 2026-03-07 - [Path Traversal in StorageManager]
**Vulnerability:** Path traversal vulnerability in `LocalStorage` where `remote_path` is directly joined with `base_path` using `os.path.join(self.base_path, remote_path)` without verifying that the resulting path is strictly contained within the base directory. A malicious user could potentially exploit this to delete arbitrary files, upload files to arbitrary locations, or check for existence of arbitrary files on the filesystem.
**Learning:** `os.path.join` does not protect against path traversal attacks if the right-hand path is an absolute path or contains `..` components. Furthermore, checking if a path starts with another using `.startswith` is vulnerable to sibling directory attacks.
**Prevention:** Always use `os.path.abspath(os.path.join(base, path))` and ensure the resulting string is strictly a sub-path using `os.path.commonpath([base, resulting_path]) == base` before proceeding with file operations.
