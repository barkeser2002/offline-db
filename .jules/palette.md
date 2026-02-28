# Palette's Journal

## 2026-03-01 - [Notifications and Search Accessibility]
**Learning:** Adding ARIA attributes to vanilla JS dropdowns and search forms is a low-effort, high-impact win for accessibility.
**Action:** Always check for `aria-label` on icon-only buttons and `aria-expanded` on custom dropdowns.

## 2026-02-26 - [Keyboard Focus Visibility]
**Learning:** Use `focus-visible` utility classes to add accessible focus rings for keyboard users without affecting mouse interactions.
**Action:** Replace `focus:outline-none` with `focus:outline-none focus-visible:ring-2` to maintain accessibility while preserving clean visual design.

## 2026-03-02 - [Native Alerts vs Custom Toasts]
**Learning:** Native `alert()` calls disrupt the user experience by blocking the browser thread and looking visually jarring. Replacing them with non-blocking, stylized toasts improves interaction smoothness significantly.
**Action:** Consistently replace `alert()` with `window.showToast()` (or equivalent) for user feedback across the application.
\n## 2026-05-18 - Missing Focus States\n**Learning:** The application extensively uses `a` and `button` tags but rarely provides visual feedback for keyboard navigation via `focus-visible`. Since `focus-visible:ring-2 focus-visible:ring-brand` is used in the nav, it should be uniformly applied across all interactive elements (like cards, buttons, inputs).\n**Action:** Apply `focus:outline-none focus-visible:ring-2 focus-visible:ring-brand` (with `focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900` for dark backgrounds where appropriate) to all missing interactive elements.
