from playwright.async_api import async_playwright
import asyncio
import ast


class SwiggyExtractService:
    def is_swiggy_restaurant_url(self, url: str) -> bool:
        if not isinstance(url, str):
            return False
        return "swiggy.com" in url and "rest" in url

    def extract_offers(self, response_data):
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
            cleaned = []
            for offer_str in offers:
                try:
                    data = ast.literal_eval(offer_str)
                    if isinstance(data, dict):
                        info = data.get("info", {})
                        header = info.get("header", "")
                        code = info.get("couponCode", "")
                        desc = info.get("description", "")

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

    def extract_99_items(self, response_data):
        try:
            items = []

            def find_99_recursive(data):
                results = []
                if isinstance(data, dict):
                    if (
                        data.get("@type")
                        == "type.googleapis.com/swiggy.presentation.food.v2.Dish"
                    ):
                        info = data.get("info", {})
                        if info.get("isNinetyninestoreItem") is True:
                            name = info.get("name")
                            if name:
                                results.append(name)

                    for k, v in data.items():
                        results.extend(find_99_recursive(v))
                elif isinstance(data, list):
                    for item in data:
                        results.extend(find_99_recursive(item))
                return results

            if response_data:
                items.extend(find_99_recursive(response_data))

            return list(set(items))
        except Exception:
            return []

    def extract_ratings(self, response_data):
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
                        ratings["totalRatingsString"] = info.get(
                            "totalRatingsString", ""
                        )
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

    def extract_offer_items(self, response_data) -> dict:
        try:
            offer_items = {}

            def find_offers_recursive(data):
                if isinstance(data, dict):
                    if (
                        data.get("@type")
                        == "type.googleapis.com/swiggy.presentation.food.v2.Dish"
                    ):
                        info = data.get("info", {})
                        category = info.get("category", "")
                        item_name = info.get("name")

                        if item_name:
                            # 1. Check Category
                            # keywords: "off", "items starting", "items at", "flat"
                            for valid_keyword in [
                                "off",
                                "items starting",
                                "items at",
                                "flat",
                            ]:
                                if valid_keyword in category.lower():
                                    if category not in offer_items:
                                        offer_items[category] = []
                                    if item_name not in offer_items[category]:
                                        offer_items[category].append(item_name)
                                    break

                            # 2. Check Offer Tags
                            offer_tags = info.get("offerTags", [])
                            if offer_tags and isinstance(offer_tags, list):
                                for tag in offer_tags:
                                    title = tag.get("title")
                                    if title:
                                        if title not in offer_items:
                                            offer_items[title] = []
                                        if item_name not in offer_items[title]:
                                            offer_items[title].append(item_name)

                    for k, v in data.items():
                        find_offers_recursive(v)
                elif isinstance(data, list):
                    for item in data:
                        find_offers_recursive(item)

            if response_data:
                find_offers_recursive(response_data)

            return offer_items
        except Exception:
            return {}

    async def extract_data(self, url: str) -> dict:
        if not self.is_swiggy_restaurant_url(url):
            return {"error": "Invalid Swiggy URL"}

        transaction_state = {"current_response": None}

        async def handle_response(response):
            if response.request.resource_type in [
                "image",
                "font",
                "stylesheet",
                "media",
            ]:
                return

            if "swiggy.com/dapi/" in response.url and response.status == 200:
                try:
                    # response.json() is async in async_playwright
                    transaction_state["current_response"] = await response.json()
                except Exception:
                    pass

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                )

                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    locale="en-IN",
                    timezone_id="Asia/Kolkata",
                    viewport={"width": 1366, "height": 768},
                )

                page = await context.new_page()
                page.on("response", handle_response)

                await page.goto(url, wait_until="networkidle", timeout=60000)

                # Wait a bit to ensure DAPI calls finish if networkidle isn't enough
                await asyncio.sleep(2)

                await browser.close()

            offers = self.extract_offers(transaction_state["current_response"])
            items_99 = self.extract_99_items(transaction_state["current_response"])
            offer_items = self.extract_offer_items(
                transaction_state["current_response"]
            )
            ratings = self.extract_ratings(transaction_state["current_response"])

            return {
                "promo_codes": offers,
                "99_store_items": items_99,
                "offer_items": offer_items,
                "rating": ratings.get("avgRatingString", ""),
                "total_ratings": ratings.get("totalRatingsString", ""),
            }

        except Exception as e:
            return {"error": str(e)}
