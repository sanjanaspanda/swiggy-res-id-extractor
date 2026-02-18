from playwright.sync_api import sync_playwright
import os
import time


def inject_cookies_and_login():
    auth_file = "data/auth_state.json"

    if not os.path.exists(auth_file):
        print(f"Error: Auth state file '{auth_file}' not found.")
        print(
            "Please run 'python generate_auth_state.py' first to log in and save your session."
        )
        return

    with sync_playwright() as p:
        # Launch headed to see the result
        browser = p.chromium.launch(
            headless=False, channel="chrome"
        )  # Attempt to use installed chrome for better compatibility, falls back if not found usually

        try:
            context = browser.new_context(
                storage_state=auth_file,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720},
            )
            print(f"Loaded authentication state from '{auth_file}'.")
        except Exception as e:
            print(f"Error loading storage state: {e}")
            return

        page = context.new_page()

        print("Navigating to Gmail...")
        page.goto("https://mail.google.com")

        print(
            "Browser is open. Press Ctrl+C to close the script and browser manually if needed, otherwise it will close when script ends (but we have a sleep)."
        )
        # Keep it open for 5 minutes so user can inspect
        time.sleep(300)

        browser.close()


if __name__ == "__main__":
    inject_cookies_and_login()
