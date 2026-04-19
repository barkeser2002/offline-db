from playwright.sync_api import Page, expect, sync_playwright

def test_admin_upload(page: Page):
    page.goto("http://localhost:3000/admin/upload")
    page.wait_for_timeout(2000)

    page.get_by_role("tab", name="Magnet Link").click()
    page.wait_for_timeout(500)

    # We will try to fill the input inside the input wrapper
    # The label is "Magnet Link / Torrent URL"
    input_field = page.locator('input[type="text"]').first
    input_field.fill("invalid-link")

    # blur the input
    page.locator('body').click()

    page.wait_for_timeout(500)
    page.screenshot(path="/home/jules/verification/admin_upload.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            test_admin_upload(page)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()
