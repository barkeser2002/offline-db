from playwright.sync_api import sync_playwright, expect

def verify_feature():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_video_dir="/home/jules/verification/video")
        page = context.new_page()
        try:
            page.goto("http://localhost:3000/admin/upload")
            page.wait_for_timeout(2000)

            # Click on Magnet Link tab
            page.get_by_role("tab", name="Magnet Link").click()
            page.wait_for_timeout(1000)

            # Locate the input field
            magnet_input = page.get_by_label("Magnet Link / Torrent URL")

            # Test empty state - button should be disabled
            start_button = page.get_by_role("button", name="Start Download")
            expect(start_button).to_be_disabled()

            # Test invalid state
            magnet_input.fill("invalid-link")
            page.wait_for_timeout(1000)

            # Check for error message and disabled button
            # Note: The error message might be rendered but visually hidden until interaction blur/focus
            # We'll trigger a blur to make sure NextUI shows it
            page.get_by_role("heading", name="Upload Content").click()
            page.wait_for_timeout(1000)

            expect(page.locator('[data-slot="error-message"]')).to_have_text("URL must start with magnet: or https://")
            expect(start_button).to_be_disabled()
            page.screenshot(path="/home/jules/verification/invalid_magnet.png")

            # Test valid state (magnet)
            magnet_input.fill("magnet:?xt=urn:btih:example")
            page.get_by_role("heading", name="Upload Content").click()
            page.wait_for_timeout(1000)
            expect(page.get_by_text("URL must start with magnet: or https://")).not_to_be_visible()
            expect(start_button).to_be_enabled()
            page.screenshot(path="/home/jules/verification/valid_magnet.png")

            # Test valid state (https)
            magnet_input.fill("https://example.com/torrent")
            page.get_by_role("heading", name="Upload Content").click()
            page.wait_for_timeout(1000)
            expect(page.get_by_text("URL must start with magnet: or https://")).not_to_be_visible()
            expect(start_button).to_be_enabled()
            page.screenshot(path="/home/jules/verification/valid_https.png")

        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    import os
    os.makedirs("/home/jules/verification/video", exist_ok=True)
    verify_feature()
