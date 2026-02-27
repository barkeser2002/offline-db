import time
from playwright.sync_api import sync_playwright

def verify_search_shortcut():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Give Next.js time to start
        context = browser.new_context()
        page = context.new_page()

        # Try to connect for up to 30 seconds
        for _ in range(10):
            try:
                page.goto("http://localhost:3000")
                break
            except Exception:
                time.sleep(3)

        # Wait for hydration
        page.wait_for_timeout(5000)

        # Check if the search input exists and has the Kbd hint
        search_input = page.locator('input[type="search"]')

        # Take a screenshot of the initial state (search bar should be visible)
        page.screenshot(path="frontend_verification_initial.png")
        print("Initial screenshot taken.")

        # Simulate Cmd+K
        page.keyboard.press("Meta+k")

        # Wait a bit for focus
        page.wait_for_timeout(500)

        # Check if the input is focused
        is_focused = search_input.evaluate("el => el === document.activeElement")
        print(f"Is search input focused? {is_focused}")

        # Take a screenshot to verify focus ring or cursor
        page.screenshot(path="frontend_verification_focused.png")
        print("Focused screenshot taken.")

        browser.close()

if __name__ == "__main__":
    verify_search_shortcut()
