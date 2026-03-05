## 2024-05-24 - Inline Contextual Actions
**Learning:** When using zero-results empty states (such as a search yielding no results with active filters), adding an inline 'Clear Filters' action directly underneath the message greatly reduces user friction and preserves contextual focus without requiring the user to navigate to a global filter control element.
**Action:** Always insert a visible, prominent Reset/Clear button within empty state layouts when empty outcomes are driven by user-set filters or configurations.
## 2024-05-19 - Missing Alt Text on Dynamic Images
**Learning:** Dynamic images rendered from API data (like episode cover images and character avatars) frequently lack `alt` attributes, as the alt text isn't a static string. This creates accessibility barriers for screen reader users who just hear the image URL or "image".
**Action:** When adding or reviewing images that consume dynamic data, ensure a descriptive `alt` attribute is constructed using the available data (e.g., ``alt={`Episode ${ep.number} thumbnail`}``) or a sensible generic fallback (e.g., `alt="Avatar"`) if specific context is missing.

## 2024-05-18 - Semantic Accessibility with NextUI Forms
**Learning:** NextUI's `Input` components don't automatically add `aria-required` or visual mandatory indicators unless the `isRequired` prop is explicitly provided. Since many configuration and profile pages (e.g., admin settings or profile data) consist of mandatory fields, neglecting `isRequired` reduces the accessibility of these forms significantly, preventing screen readers from clearly announcing their status.
**Action:** When working on form inputs with NextUI, always determine if a field is logically mandatory and, if so, ensure the `isRequired` prop is included to provide semantic accessibility context (`aria-required="true"`) and visual asterisks for sighted users.

## 2024-05-25 - Quick Input Reset Contextual Actions
**Learning:** NextUI `<Input>` components used for search or extensive text entry can trap users when they want to clear their query or text input to reset their view. Providing the built-in `isClearable` prop (and `onClear` for controlled inputs) adds a critical inline contextual action (an 'X' button) to clear the query, improving the usability of filters and search bars.
**Action:** Always provide `isClearable` and `onClear` properties to NextUI `Input` elements used for search filtering to give users a quick way to reset their input state.
