import pandas as pd
import re
import time
import random
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from playwright.sync_api import sync_playwright

INPUT_CSV = "restaurants_with_ids_for_agnostic_test.csv"
OUTPUT_CSV = "output.csv"
MAX_WORKERS = 4  # Adjust based on your CPU cores and memory


def is_swiggy_restaurant_url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    return "swiggy.com" in url and "rest" in url


def extract_offers(response_data):
    try:
        offers = []

        def find_key_recursive(data, target):
            results = []
            if isinstance(data, dict):
                for k, v in data.items():
                    if k == target:
                        results.append(str(v))
                    results.extend(find_key_recursive(v, target))
            elif isinstance(data, list):
                for item in data:
                    results.extend(find_key_recursive(item, target))
            return results

        if response_data:
            offers.extend(find_key_recursive(response_data, "offers"))

        # Clean + de-duplicate
        import ast

        cleaned = []
        for offer_str in offers:
            try:
                # Parse the stringified dictionary back into a Python object
                data = ast.literal_eval(offer_str)
                if isinstance(data, dict):
                    info = data.get("info", {})
                    header = info.get("header", "")
                    code = info.get("couponCode", "")
                    desc = info.get("description", "")

                    # Combine the requested fields
                    display_text = " | ".join(filter(None, [header, code, desc]))
                    if display_text and display_text not in cleaned:
                        cleaned.append(display_text)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            info = item.get("info", {})
                            header = info.get("header", "")
                            code = info.get("couponCode", "")
                            desc = info.get("description", "")

                            # Combine the requested fields
                            display_text = " | ".join(
                                filter(None, [header, code, desc])
                            )
                            if display_text and display_text not in cleaned:
                                cleaned.append(display_text)

            except Exception:
                continue
        return cleaned
    except Exception:
        return []


def extract_99_items(response_data):
    try:
        items = []

        def find_99_recursive(data):
            results = []
            if isinstance(data, dict):
                # Check for the specific type value
                if (
                    data.get("@type")
                    == "type.googleapis.com/swiggy.presentation.food.v2.Dish"
                ):
                    # Check for isNinetyninestoreItem flag in info
                    info = data.get("info", {})
                    if info.get("isNinetyninestoreItem") is True:
                        name = info.get("name")
                        if name:
                            results.append(name)

                # Continue recursion
                for k, v in data.items():
                    results.extend(find_99_recursive(v))
            elif isinstance(data, list):
                for item in data:
                    results.extend(find_99_recursive(item))
            return results

        if response_data:
            items.extend(find_99_recursive(response_data))

        # Deduplicate
        return list(set(items))
    except Exception:
        return []


def extract_ratings(response_data):
    try:
        ratings = {"avgRatingString": "", "totalRatingsString": ""}

        def find_restaurant_recursive(data):
            if isinstance(data, dict):
                if (
                    data.get("@type")
                    == "type.googleapis.com/swiggy.presentation.food.v2.Restaurant"
                ):
                    info = data.get("info", {})
                    ratings["avgRatingString"] = info.get("avgRatingString", "")
                    ratings["totalRatingsString"] = info.get("totalRatingsString", "")
                    return True  # Stop recursion once found

                for k, v in data.items():
                    if find_restaurant_recursive(v):
                        return True
            elif isinstance(data, list):
                for item in data:
                    if find_restaurant_recursive(item):
                        return True
            return False

        if response_data:
            find_restaurant_recursive(response_data)

        return ratings
    except Exception:
        return {"avgRatingString": "", "totalRatingsString": ""}


def process_chunk(df_chunk):
    """
    Process a chunk of the dataframe with its own Playwright instance.
    """
    # Needs to capture response per page
    # using a Mutable container (list) because simple variable assignment in closure would fail without nonlocal
    # Dict is also mutable, which is good.
    transaction_state = {"current_response": None}

    def handle_response(response):
        # Filter out noisy resources like images, fonts, and styles for cleaner output
        if response.request.resource_type in ["image", "font", "stylesheet", "media"]:
            return

        # Specifically look for Swiggy DAPI calls which likely contain the data
        if "swiggy.com/dapi/" in response.url and response.status == 200:
            try:
                transaction_state["current_response"] = response.json()
            except Exception:
                pass

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, args=["--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            viewport={"width": 1366, "height": 768},
        )

        page = context.new_page()
        page.on("response", handle_response)

        for idx, row in df_chunk.iterrows():
            swiggy_url = row.get("swiggy res id", "")

            if not is_swiggy_restaurant_url(swiggy_url):
                continue

            print(f"Scraping: {row['Restaurant Name']}")

            # Reset captured data for this iteration
            transaction_state["current_response"] = None

            try:
                page.goto(swiggy_url, wait_until="networkidle", timeout=60000)

                # Extract using the captured response data
                offers = extract_offers(transaction_state["current_response"])
                items_99 = extract_99_items(transaction_state["current_response"])
                ratings = extract_ratings(transaction_state["current_response"])

                if offers:
                    df_chunk.at[idx, "promo_codes"] = f"({', '.join(offers)})"
                else:
                    df_chunk.at[idx, "promo_codes"] = "()"

                if items_99:
                    df_chunk.at[idx, "99_store_items"] = f"({', '.join(items_99)})"
                else:
                    df_chunk.at[idx, "99_store_items"] = "()"

                df_chunk.at[idx, "rating"] = ratings["avgRatingString"]
                df_chunk.at[idx, "total_ratings"] = ratings["totalRatingsString"]

                time.sleep(random.randint(2, 4))

            except Exception as e:
                print(f"Failed for {swiggy_url}: {e}")
                df_chunk.at[idx, "promo_codes"] = "()"
                df_chunk.at[idx, "99_store_items"] = "()"
                df_chunk.at[idx, "rating"] = ""
                df_chunk.at[idx, "total_ratings"] = ""

        browser.close()

    return df_chunk


def main():
    try:
        df = pd.read_csv(INPUT_CSV)
    except FileNotFoundError:
        print(f"Error: {INPUT_CSV} not found.")
        return

    if "promo_codes" not in df.columns:
        df["promo_codes"] = ""
    if "99_store_items" not in df.columns:
        df["99_store_items"] = ""
    if "rating" not in df.columns:
        df["rating"] = ""
    if "total_ratings" not in df.columns:
        df["total_ratings"] = ""

    # Filter valid URLs to count actual work?
    # Keeping logic simple: split everything.

    num_rows = len(df)
    if num_rows == 0:
        print("Empty input CSV.")
        return

    num_chunks = MAX_WORKERS
    if num_rows < num_chunks:
        num_chunks = num_rows  # Avoid empty chunks if fewer rows than workers

    print(f"Starting scraping with {num_chunks} workers for {num_rows} rows...")

    chunks = np.array_split(df, num_chunks)

    processed_chunks = []
    # Use spawn context if on Windows/macOS mainly, but default ProcessPoolExecutor usually handles this.
    # On Windows, all args must be picklable.

    with ProcessPoolExecutor(max_workers=num_chunks) as executor:
        results = executor.map(process_chunk, chunks)
        for res in results:
            processed_chunks.append(res)

    # Combine results
    if processed_chunks:
        final_df = pd.concat(processed_chunks)
        final_df.to_csv(OUTPUT_CSV, index=False)
        print(f"\n✅ Done. Output saved to {OUTPUT_CSV}")
    else:
        print("No results generated.")


if __name__ == "__main__":
    main()
