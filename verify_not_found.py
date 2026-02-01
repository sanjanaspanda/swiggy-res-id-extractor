import asyncio
from playwright.async_api import async_playwright
from app.services.search_service import SwiggySearchService


async def verify():
    # Use the known problematic URL
    url = "https://www.swiggy.com/city/mumbai/javaphile-pali-hill-rest375316"
    print(f"Verifying Not Found Logic for: {url}")

    service = SwiggySearchService()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Navigating...")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(2)  # Allow for any client-side renders

        print("Checking _is_not_found...")
        is_not_found = await service._is_not_found(page)

        if is_not_found:
            print("✅ CORRECT: Identified as 'Not Found'")
        else:
            print("❌ INCORRECT: Failed to identify as 'Not Found'")

            # Debug info
            print(f"Title: {await page.title()}")
            uhoh = await page.get_by_text("Uh-oh!", exact=False).is_visible()
            print(f"Visible 'Uh-oh!': {uhoh}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(verify())
