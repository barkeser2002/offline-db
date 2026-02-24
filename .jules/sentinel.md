## 2025-02-18 - Websocket Stored XSS
**Vulnerability:** Chat messages in `WatchPartyConsumer` were saved and broadcast without sanitization, allowing Stored XSS.
**Learning:** Websockets often bypass standard Django template auto-escaping if messages are handled manually.
**Prevention:** Always sanitize user input in consumers before saving or broadcasting, especially if frontend rendering is uncertain.
