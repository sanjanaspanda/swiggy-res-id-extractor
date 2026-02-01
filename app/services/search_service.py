from playwright.async_api import async_playwright
from playwright_stealth.stealth import Stealth
import asyncio
import difflib
import re
from pprint import pprint


class SwiggySearchService:
    import pandas as pd
    import os

    # List of realistic user-agents (update periodically)
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _data_path = os.path.join(_current_dir, "../../data/user_agents.tsv")

    user_agents = pd.read_csv(_data_path, sep="\t")["User Agents"].tolist()

    async def handle_response(self, response) -> str:
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
                self.current_response = await response.json()
            except Exception as e:
                print("Error parsing response", e)

    async def _is_not_found(self, page) -> bool:
        """
        Check for specific Swiggy 'Not Found' indicators.
        """
        try:
            # 1. Check for explicit error text indicators on the page
            # These are robust and should override any title heuristics

            # "Uh-oh!" is a common Swiggy error header
            if (
                await page.get_by_text("Uh-oh!", exact=False).is_visible()
                and not await page.get_by_text(
                    "Uh-oh! Outlet is not accepting orders at the moment.", exact=False
                ).is_visible()
            ):
                return True

            # "Sorry! This should not have happened" is the subtext
            if await page.get_by_text(
                "Sorry! This should not have happened", exact=False
            ).is_visible():
                return True

            # 2. Check Title
            title = await page.title()
            title_lower = title.strip().lower()

            if title_lower in ["page not found", "movie not found"]:
                return True

            # 3. Check for "Page Not Found" text specifically if it's large/visible
            not_found_text = page.get_by_text("Page Not Found", exact=True)
            if await not_found_text.count() > 0 and await not_found_text.is_visible():
                return True

            return False
        except Exception:
            return False

    async def find_restaurant_url(self, restaurant_name: str, location: str) -> dict:
        result = {
            "url": None,
            "dineout_only": False,
            "not_found": False,
            "error": None,
        }
        not_found_count = 0

        query = f"{restaurant_name}, {location} swiggy"
        candidate_url_str = None

        # --- PHASE 1: SEARCH (Using Stealth for DDG) ---
        try:
            async with Stealth().use_async(async_playwright()) as p:
                browser = await p.chromium.launch(
                    headless=False,
                    channel="chrome",
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                    ],
                )

                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1366, "height": 768},
                    locale="en-IN",
                    timezone_id="Asia/Kolkata",
                )

                try:
                    page = await context.new_page()
                    # page.on("response", self.handle_response) # Not needed for search phase really

                    await page.goto("https://duckduckgo.com/")

                    # Search Logic
                    search_input = page.locator('[name="q"]')
                    if await search_input.count() == 0:
                        search_input = page.locator("#searchbox_input")

                    if await search_input.count() > 0:
                        await search_input.fill(query)
                        await asyncio.sleep(1)
                        await search_input.press("Enter")

                        try:
                            await page.wait_for_selector(
                                ".react-results--main", timeout=5000
                            )
                        except Exception:
                            await page.wait_for_load_state("networkidle")

                    links = await page.locator(
                        'a[href*="swiggy.com/restaurants"], a[href*="swiggy.com/city"]'
                    ).all()
                    print("Links found:", len(links))
                    pprint(links)
                    if links:
                        candidate_url_str = await self._process_links_and_get_url(
                            links, location, restaurant_name
                        )
                    else:
                        if await self._is_captcha_page(page):
                            result["error"] = "Captcha detected during search"
                            result["not_found"] = True
                            return result
                        result["not_found"] = True
                        result["error"] = "No search results found"
                        return result

                finally:
                    await browser.close()

        except Exception as e:
            result["error"] = f"Search Phase Error: {str(e)}"
            result["not_found"] = True
            return result

        if not candidate_url_str:
            if not result["error"]:
                result["not_found"] = True
                result["error"] = "No suitable link found"
            return result

        print(f"Candidate URL found: {candidate_url_str}")

        # --- PHASE 2: VALIDATION (Using Standard Playwright for Swiggy) ---
        try:
            async with async_playwright() as p:
                # Standard Launch (matching extract_service)
                browser = await p.chromium.launch(
                    headless=False,
                    channel="chrome",
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                    ],
                )

                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1366, "height": 768},
                    locale="en-IN",
                    timezone_id="Asia/Kolkata",
                )
                try:
                    page = await context.new_page()

                    # Check Main URL
                    try:
                        await page.goto(
                            candidate_url_str, wait_until="networkidle", timeout=60000
                        )
                    except Exception as e:
                        print(f"Navigation error: {e}")

                    await asyncio.sleep(3)
                    while not_found_count < 2:
                        not_found_result = await self._is_not_found(page)
                        if not not_found_result:
                            result["url"] = page.url
                            result["not_found"] = False
                            return result
                        not_found_count += 1
                        await page.reload()

                    # Check Dineout
                    base_url = candidate_url_str.rstrip("/")
                    dineout_url = f"{base_url}/dineout"

                    try:
                        await page.goto(
                            dineout_url, wait_until="networkidle", timeout=60000
                        )
                    except Exception:
                        pass

                    await asyncio.sleep(3)

                    not_found_dineout = await self._is_not_found(page)
                    if not not_found_dineout:
                        result["url"] = page.url
                        result["dineout_only"] = True
                        result["not_found"] = False
                        return result

                    # Both Failed
                    result["not_found"] = True
                    result["error"] = "Restaurant not found (both delivery and dineout)"
                    result["url"] = candidate_url_str
                    return result

                finally:
                    await browser.close()

        except Exception as e:
            result["error"] = f"Validation Phase Error: {str(e)}"
            result["not_found"] = True
            return result

    async def _process_links_and_get_url(self, links, location, restaurant_name) -> str:
        """
        Helper to select the best URL from search results.
        Returns the raw URL string or None.
        """
        from urllib.parse import unquote

        MIN_NAME_SCORE = 0.45

        def normalize(s: str) -> str:
            if not s:
                return ""
            s = unquote(s.lower())
            s = re.sub(r"[^a-z0-9\s\-\/]", " ", s)
            return s

        restaurant_tokens = restaurant_name.lower().split()
        location_tokens = location.lower().split()

        candidates = []

        for link in links:
            try:
                text_raw = await link.inner_text()
                href_raw = await link.get_attribute("href")

                if not href_raw:
                    continue
                if "/restaurants/" not in href_raw and "/city/" not in href_raw:
                    continue

                text = normalize(text_raw)
                href = normalize(href_raw)

                # Validate URL structure (must end with number or rest<number>)
                # Clean query params first if any (though normalize keeps them usually, let's look at raw href logic)
                # Ideally check the href path.
                url_path = href_raw.split("?")[0].rstrip("/")
                if not re.search(r"-(?:rest)?\d+$", url_path):
                    continue

                slug = ""
                try:
                    parts = [p for p in href_raw.split("/") if p]
                    if "restaurants" in parts:
                        slug = parts[parts.index("restaurants") + 1]
                    elif "city" in parts:
                        slug = parts[-1]
                    slug = slug.replace("-", " ").lower()
                except Exception:
                    pass

                text_score = difflib.SequenceMatcher(
                    None, restaurant_name.lower(), text
                ).ratio()
                slug_score = difflib.SequenceMatcher(
                    None, restaurant_name.lower(), slug
                ).ratio()
                score = max(text_score, slug_score)

                slug_token_match = all(t in slug for t in restaurant_tokens)

                if score < MIN_NAME_SCORE and not slug_token_match:
                    continue

                candidates.append(
                    {
                        "href": href,
                        "raw_href": href_raw,
                        "text": text,
                        "slug": slug,
                        "score": score,
                        "slug_match": slug_token_match,
                    }
                )
            except Exception:
                continue

        if not candidates:
            return None

        # Location Priority
        strong_matches = []
        loose_matches = []

        for c in candidates:
            href = c["href"]
            haystack = f"{c['text']} {href}"
            strong = all(t in href for t in location_tokens) and "rest" in href
            loose = all(t in haystack for t in location_tokens)

            if strong:
                strong_matches.append(c)
            elif loose:
                loose_matches.append(c)

        chosen = None
        if strong_matches:
            chosen = sorted(
                strong_matches,
                key=lambda x: (x["slug_match"], x["score"]),
                reverse=True,
            )[0]
        elif loose_matches:
            chosen = sorted(
                loose_matches, key=lambda x: (x["slug_match"], x["score"]), reverse=True
            )[0]
        elif candidates:
            chosen = sorted(
                candidates, key=lambda x: (x["slug_match"], x["score"]), reverse=True
            )[0]

        if not chosen:
            return None

        url = chosen["raw_href"]
        # Normalize: strip dineout/menu
        url = url.replace("/dineout", "").rstrip("/")
        if url.endswith("/menu"):
            url = url[:-5]

        return url

    async def _is_captcha_page(self, page) -> bool:
        try:
            title = await page.title()
            if "sorry" in title.lower() or "robot" in title.lower():
                return True
            if await page.get_by_text("unusual traffic", exact=False).count() > 0:
                return True
            if await page.get_by_text("I'm not a robot", exact=False).count() > 0:
                return True
            return False
        except Exception:
            return False
