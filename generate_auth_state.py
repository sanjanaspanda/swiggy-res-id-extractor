from playwright.sync_api import sync_playwright
import os


def generate_auth_state():
    auth_file = "data/auth_state.json"

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Create a directory for the persistent profile
    profile_dir = "data/chrome_profile"
    os.makedirs(profile_dir, exist_ok=True)

    with sync_playwright() as p:
        print("Launching browser for manual login (Persistent Context)...")
        # Use launch_persistent_context which is much harder for Google to detect as automation
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            channel="chrome",
            headless=False,
            # Key arguments to look like a real browser
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
            ],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        )

        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://accounts.google.com")

        print("\n" + "=" * 50)
        print(
            "ACTION REQUIRED: Please log in to your Google account in the browser window."
        )
        print(
            "Once you are fully logged in and can see your account dashboard or inbox, return here."
        )
        input("Press Enter here to save the authentication state and exit...")
        print("=" * 50 + "\n")

        # Save storage state
        context.storage_state(path=auth_file)
        print(f"Authentication state saved to '{auth_file}'.")

        context.close()


if __name__ == "__main__":
    generate_auth_state()
