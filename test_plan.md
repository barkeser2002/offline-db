1. **Identify Vulnerability**: In `apps/watchparty/views.py`, the `RoomViewSet` inherits from `viewsets.ModelViewSet` which allows any authenticated user to update or delete any room because there is no authorization check. This is an IDOR vulnerability.
2. **Implement Fix**: Create a custom permission class `IsHostOrReadOnly` (or similar logic directly in the view) to enforce that only the `host` of a room can modify or delete it. Alternatively, override `perform_update` and `perform_destroy` to raise `PermissionDenied` if `request.user != instance.host`.
3. **Write/Run Tests**: Run the existing test suite (using `USE_SQLITE=True pytest`). Add a small test if necessary.
4. **Pre-commit**: Complete the required pre-commit checks.
5. **Submit**: Create the PR for Sentinel.
