from playwright.sync_api import sync_playwright
import re
import csv
from concurrent.futures import ThreadPoolExecutor


def do_search(restaurant_name, location):
    query = f"{restaurant_name} {location} swiggy"
    with sync_playwright() as p:
        # Launch with stealth arguments
        browser = p.chromium.launch(
            headless=False, args=["--disable-blink-features=AutomationControlled"]
        )
        # Use a realistic User Agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Add init script to remove webdriver property
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = context.new_page()
        page.goto("https://www.google.com")

        # Human-like typing delay
        import random
        import time

        page.fill('textarea[name="q"]', query)
        time.sleep(random.uniform(0.5, 1.5))  # Random delay

        page.press('textarea[name="q"]', "Enter")
        # Using a slightly longer wait strategy to ensure results populate
        try:
            page.wait_for_selector("#search", timeout=5000)
        except:
            page.wait_for_load_state("networkidle")

        # Handle "Not now" location popup if it appears
        try:
            not_now_btn = page.get_by_text("Not now")
            if not_now_btn.is_visible(timeout=3000):
                not_now_btn.click()
                time.sleep(1)
        except Exception:
            pass

        time.sleep(random.uniform(1.0, 2.0))

        # Get all Swiggy restaurant/city links
        links = page.locator(
            'a[href*="swiggy.com/restaurants"], a[href*="swiggy.com/city"]'
        ).all()

        if not links:
            print(f"No Swiggy links found for {restaurant_name} ({location})")
            return "No Results Found"

        normalized_target_location = location.lower().replace(" ", "")

        candidates = []
        for link in links:
            try:
                text = link.inner_text().lower().replace("\n", " ")
                href = link.get_attribute("href")
                # Classify as restaurant or city/collection
                is_restaurant_link = "/restaurants/" in href

                candidates.append(
                    {
                        "element": link,
                        "text": text,
                        "href": href,
                        "is_restaurant": is_restaurant_link,
                    }
                )
            except Exception:
                continue

        # Strategy Refined:
        # 1. Restaurant Link matching Location.
        # 2. Restaurant Link (Any - likely "nearby" fallback).
        # 3. City Link matching Location.
        # 4. First Link.

        chosen_link = None
        match_type = ""

        # 1. Restaurant Link + Location Match
        for c in candidates:
            if c["is_restaurant"]:
                if (
                    normalized_target_location in c["text"].replace(" ", "")
                    or normalized_target_location in c["href"].replace("-", "").lower()
                ):
                    chosen_link = c["element"]
                    match_type = "Exact Restaurant Match"
                    break

        # 2. Restaurant Link (Any - likely "nearby" fallback)
        if not chosen_link:
            for c in candidates:
                if c["is_restaurant"]:
                    chosen_link = c["element"]
                    match_type = "Fallback to Restaurant Link"
                    break

        # 3. City Link + Location Match
        if not chosen_link:
            for c in candidates:
                if (
                    normalized_target_location in c["text"].replace(" ", "")
                    or normalized_target_location in c["href"].replace("-", "").lower()
                ):
                    chosen_link = c["element"]
                    match_type = "Location Match (City Link)"
                    break

        if not chosen_link and candidates:
            chosen_link = candidates[0]["element"]
            match_type = "First Result Fallback"

        if not chosen_link:
            return "No Suitable Link Found"

        if not chosen_link:
            return "No Suitable Link Found"

        original_href = chosen_link.get_attribute("href")
        print(f"Selected matched link: {original_href}")

        # Check for Dineout
        final_url = original_href
        if "dineout" in original_href.lower():
            # Try removing dineout
            # Common patterns: ".../dineout" at end or ".../dineout/..."
            # Simple approach: remove '/dineout' and see
            clean_href = (
                original_href.lower().replace("/dineout", "").replace("dineout/", "")
            )
            print(f"Dineout detected. Trying clean URL: {clean_href}")

            try:
                page.goto(clean_href)
                page.wait_for_load_state("networkidle")

                # Check validation
                title = page.title()
                is_404 = (
                    "Page Not Found" in title
                    or page.get_by_text("Page Not Found", exact=False).count() > 0
                )

                if not is_404:
                    print("Clean URL is valid. Using it.")
                    return page.url
                else:
                    print("Clean URL failed (404 or Homepage). Reverting to original.")
            except Exception as e:
                print(f"Error checking clean URL: {e}")

        # If clean failed or wasn't dineout, go to original
        try:
            if page.url != final_url:  # Only navigate if not already there
                page.goto(final_url)
                page.wait_for_load_state("networkidle")
        except Exception:
            return "Network Error"

        if (
            "Page Not Found" in page.title()
            or page.get_by_text("Page Not Found", exact=False).count() > 0
        ):
            return "Page Not Found"

        print(f"Result URL: {page.url}")
        return page.url


def process_row(row):
    try:
        # Pass name and location explicitly
        row["swiggy res id"] = do_search(row["Restaurant Name"], row["Location"])
    except Exception as e:
        print(f"Error processing {row['Restaurant Name']}: {e}")
        row["swiggy res id"] = "Error"
    return row


def main():
    input_file = "restaurants.csv"
    output_file = "restaurants_with_ids.csv"

    rows = []
    with open(input_file, mode="r", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        rows = list(reader)
        fieldnames = reader.fieldnames + ["swiggy res id"]

    # Run in parallel with ThreadPoolExecutor
    # You can adjust max_workers based on your system capabilities
    processed_rows = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        processed_rows = list(executor.map(process_row, rows))

    with open(output_file, mode="w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_rows)

    print(f"Done! Processed {len(processed_rows)} restaurants. Saved to {output_file}")
    return


if __name__ == "__main__":
    main()
