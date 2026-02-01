from playwright.async_api import async_playwright
import asyncio


async def inspect_robust():
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
            await asyncio.sleep(2)

            print("\n--- TEXT INDICATORS ---")
            for text in ["Uh-oh!", "Page not found", "Sorry", "Retry", "Go Back"]:
                count = await page.get_by_text(text, exact=False).count()
                print(f"Text '{text}': {count} occurrences")

            print("\n--- IMG INDICATORS ---")
            imgs = await page.get_by_role("img").all()
            for i, img in enumerate(imgs):
                alt = await img.get_attribute("alt")
                src = await img.get_attribute("src")
                print(f"Img {i}: alt='{alt}', src='{src}'")

            print("\n--- BUTTON INDICATORS ---")
            buttons = await page.get_by_role("button").all()
            for i, btn in enumerate(buttons):
                txt = await btn.inner_text()
                print(f"Button {i}: '{txt}'")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(inspect_robust())
