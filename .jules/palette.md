## 2024-05-24 - Inline Contextual Actions
**Learning:** When using zero-results empty states (such as a search yielding no results with active filters), adding an inline 'Clear Filters' action directly underneath the message greatly reduces user friction and preserves contextual focus without requiring the user to navigate to a global filter control element.
**Action:** Always insert a visible, prominent Reset/Clear button within empty state layouts when empty outcomes are driven by user-set filters or configurations.
## 2024-05-19 - Missing Alt Text on Dynamic Images
**Learning:** Dynamic images rendered from API data (like episode cover images and character avatars) frequently lack `alt` attributes, as the alt text isn't a static string. This creates accessibility barriers for screen reader users who just hear the image URL or "image".
**Action:** When adding or reviewing images that consume dynamic data, ensure a descriptive `alt` attribute is constructed using the available data (e.g., ``alt={`Episode ${ep.number} thumbnail`}``) or a sensible generic fallback (e.g., `alt="Avatar"`) if specific context is missing.
