## YYYY-MM-DD - Sentinel Journal
**Vulnerability:** RoomViewSet lacks authorization checks for update/delete. Any authenticated user can modify or delete ANY room by sending PUT/DELETE requests to `/api/watch-parties/{uuid}/`.
**Learning:** ModelViewSet provides `update` and `destroy` actions by default. Without custom permissions (like `IsHostOrReadOnly`) or overriding `get_queryset()` to filter by user for unsafe methods, IDOR vulnerabilities are introduced.
**Prevention:** Override `perform_update` and `perform_destroy` to check `instance.host == self.request.user`, or use a custom permission class, or filter `get_queryset()`.

## 2026-03-08 - [Clickjacking via X-Frame-Options]
**Vulnerability:** `X_FRAME_OPTIONS` was set to `'SAMEORIGIN'` allowing the site to be framed by pages on the same origin. While safer than no restriction, it still leaves a minor clickjacking risk if an attacker can host malicious content on the same origin (e.g., via file upload vulnerabilities).
**Learning:** Explicitly denying all framing offers the highest level of protection against clickjacking.
**Prevention:** Set `X_FRAME_OPTIONS = 'DENY'` in Django settings to completely block the site from being rendered within a `<frame>`, `<iframe>`, `<embed>`, or `<object>`.

## 2026-03-08 - [Insecure Session Cookies]
**Vulnerability:** `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, and `SESSION_COOKIE_SAMESITE` were either missing or conditionally enabled only in production.
**Learning:** Session cookies must always be transmitted securely and protected from client-side scripts to prevent session hijacking via XSS or network interception.
**Prevention:** Explicitly define `SESSION_COOKIE_SECURE = True`, `SESSION_COOKIE_HTTPONLY = True`, and `SESSION_COOKIE_SAMESITE = 'Lax'` in settings to enforce secure cookie handling.

## 2026-03-08 - [Missing CSRF Trusted Origins]
**Vulnerability:** The `CSRF_TRUSTED_ORIGINS` setting was missing, preventing secure cross-origin requests from functioning correctly when Django is deployed behind certain proxies or specific domain structures.
**Learning:** When deploying Django to modern environments, explicitly defining trusted origins for CSRF is necessary, especially if the site relies on specific HTTPS domains or handles cross-site POST requests.
**Prevention:** Read `CSRF_TRUSTED_ORIGINS` from environment variables, allowing dynamic configuration of trusted domains in production environments (e.g., `os.getenv('CSRF_TRUSTED_ORIGINS', '...').split(',')`).

## 2024-05-24 - [Exposed Video Encryption Key]
**Vulnerability:** The `encryption_key` field was included in the `VideoFileSerializer`, exposing the HLS video encryption key in plain text via the API.
**Learning:** Django Rest Framework's `ModelSerializer` will expose sensitive fields if they are explicitly listed in the `fields` array of the `Meta` class, bypassing the intended secure serving mechanisms (like `KeyServeView`).
**Prevention:** Never include sensitive fields (passwords, encryption keys, tokens) in standard API serializers unless explicitly required and protected. Serve them securely via dedicated endpoints with appropriate authentication and authorization checks.

## 2026-03-07 - [Path Traversal in StorageManager]
**Vulnerability:** Path traversal vulnerability in `LocalStorage` where `remote_path` is directly joined with `base_path` using `os.path.join(self.base_path, remote_path)` without verifying that the resulting path is strictly contained within the base directory. A malicious user could potentially exploit this to delete arbitrary files, upload files to arbitrary locations, or check for existence of arbitrary files on the filesystem.
**Learning:** `os.path.join` does not protect against path traversal attacks if the right-hand path is an absolute path or contains `..` components. Furthermore, checking if a path starts with another using `.startswith` is vulnerable to sibling directory attacks.
**Prevention:** Always use `os.path.abspath(os.path.join(base, path))` and ensure the resulting string is strictly a sub-path using `os.path.commonpath([base, resulting_path]) == base` before proceeding with file operations.
