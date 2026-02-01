import asyncio
from app.services.search_service import SwiggySearchService
from app.services.extract_service import SwiggyExtractService


async def debug_issues():
    search_service = SwiggySearchService()
    extract_service = SwiggyExtractService()

    print("--- DEBUGGING JAVAPHILE (False Positive) ---")
    # This URL was reported as "On Swiggy" but should be Not Found
    # effectively it means search_service.find_restaurant_url returned it as valid
    javaphile_query = "Javaphile, Pali Hill, Bandra West"
    print(f"Searching for: {javaphile_query}")
    res = await search_service.find_restaurant_url(
        "Javaphile", "Pali Hill, Bandra West"
    )
    print(f"Search Result: {res}")

    if isinstance(res, dict) and not res.get("not_found") and res.get("url"):
        print("❌ FAILED: Javaphile still found as valid.")

        # Let's also verify if extract service catches it or just returns empty
        print("Attempting extraction on this bad URL...")
        ext_res = await extract_service.extract_data(res["url"])
        print(f"Extraction Result: {ext_res}")
    else:
        print("✅ PASSED: Javaphile correctly identified as Not Found.")

    print("\n--- DEBUGGING SWATI SNACKS (Missing Promos) ---")
    swati_query = "Swati Snacks, Nariman Point"
    # First find the URL
    print(f"Searching for: {swati_query}")
    res_swati = await search_service.find_restaurant_url(
        "Swati Snacks", "Nariman Point"
    )
    print(f"Swati Search Result: {res_swati}")

    if isinstance(res_swati, dict) and res_swati.get("url"):
        url = res_swati["url"]
        print(f"Extracting from: {url}")
        ext_data = await extract_service.extract_data(url)
        print("Promos Found:", ext_data.get("promo_codes"))
        print("Offers Found:", ext_data.get("offer_items"))

        if not ext_data.get("promo_codes"):
            print("❌ FAILED: No promos found for Swati Snacks.")
        else:
            print("✅ PASSED: Promos found.")


if __name__ == "__main__":
    asyncio.run(debug_issues())
