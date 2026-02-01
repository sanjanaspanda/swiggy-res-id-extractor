from playwright.async_api import async_playwright
import asyncio


async def inspect():
    url = "https://www.swiggy.com/city/mumbai/javaphile-pali-hill-rest375316"
    print(f"Inspecting: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)  # Wait for any client-side rendering

            title = await page.title()
            print(f"Title: {title}")

            # Check for current Not Found indicators
            uh_oh = await page.locator("text=Uh-oh!").count()
            print(f"Count 'Uh-oh!': {uh_oh}")

            sorry = await page.locator(
                "text=Sorry! This should not have happened"
            ).count()
            print(f"Count 'Sorry!': {sorry}")

            page_not_found = await page.get_by_text(
                "Page Not Found", exact=True
            ).count()
            print(f"Count 'Page Not Found': {page_not_found}")

            # Dump some text to see what IS there
            body_text = await page.inner_text("body")
            print("\n--- BODY TEXT START ---")
            print(body_text[:1000])  # Print first 1000 chars
            print("--- BODY TEXT END ---\n")

            # Check for generic swiggy error classes
            error_container = await page.locator("._3dbwz").count()
            print(f"Count '._3dbwz' (Error Container): {error_container}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(inspect())
