from playwright.sync_api import sync_playwright
import os

def verify_navbar():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Go to homepage
        print("Navigating to homepage...")
        try:
            page.goto("http://localhost:3000")
            # Wait for content to load, maybe the hero section or navbar
            page.wait_for_selector('nav', timeout=10000)
        except Exception as e:
            print(f"Error navigating: {e}")
            browser.close()
            return

        print("Page loaded.")

        # Verify Search Input (Desktop)
        try:
            # Look for input with aria-label="Search anime"
            # Since NextUI Input might wrap the actual input element, we look for the input element itself
            search_input = page.locator('input[aria-label="Search anime"]').first
            if search_input.is_visible():
                print("✅ Found search input with aria-label='Search anime'")
            else:
                # Maybe it's hidden on small screens? But default launch size is usually 1280x720
                print("❌ Search input found but not visible? Check viewport size.")
        except Exception as e:
            print(f"Error finding search input: {e}")

        # Verify Notification Button
        try:
            # Look for button with aria-label="Notifications"
            notification_btn = page.locator('button[aria-label="Notifications"]').first
            if notification_btn.is_visible():
                print("✅ Found notification button with aria-label='Notifications'")
            else:
                print("❌ Notification button found but not visible")
        except Exception as e:
            print(f"Error finding notification button: {e}")

        # Screenshot
        screenshot_path = "verification_navbar.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

        browser.close()

if __name__ == "__main__":
    verify_navbar()
