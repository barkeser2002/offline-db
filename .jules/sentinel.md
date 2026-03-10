## YYYY-MM-DD - Sentinel Journal
**Vulnerability:** RoomViewSet lacks authorization checks for update/delete. Any authenticated user can modify or delete ANY room by sending PUT/DELETE requests to `/api/watch-parties/{uuid}/`.
**Learning:** ModelViewSet provides `update` and `destroy` actions by default. Without custom permissions (like `IsHostOrReadOnly`) or overriding `get_queryset()` to filter by user for unsafe methods, IDOR vulnerabilities are introduced.
**Prevention:** Override `perform_update` and `perform_destroy` to check `instance.host == self.request.user`, or use a custom permission class, or filter `get_queryset()`.
## 2025-03-01 - Prevent Path Traversal in Storage Gateway
**Vulnerability:** `LocalStorage` backend in `core/storage.py` used `os.path.join` without verifying that the resolved path stayed within the intended base directory.
**Learning:** Even if current internal usages hardcode the path structure, storage modules must act as secure boundaries to prevent future path traversal bugs (LFI/Arbitrary File Write) if new features expose the path to user input.
**Prevention:** Always validate constructed file paths against a strict base directory prefix using `os.path.abspath`.
