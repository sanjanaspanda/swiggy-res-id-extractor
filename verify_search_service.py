import asyncio
import sys
import os

# Add the project root to the python path to import app modules
sys.path.append(os.getcwd())

from app.services.search_service import SwiggySearchService


async def verify_search():
    service = SwiggySearchService()

    # 1. Test standard search (should work normally)
    print("\n1. Standard Search: 'Pizza Hut' in 'Mumbai'...")
    try:
        result = await service.find_restaurant_url("Pizza Hut", "Mumbai")
        print(f"SEARCH RETURNED: {result}")
        url = result.get("url", "") if isinstance(result, dict) else str(result)
        if url and "swiggy.com" in url:
            print("✅ Standard search valid.")
        else:
            print("❌ Standard search failed.")
    except Exception as e:
        print(f"❌ Error: {e}")

    # 2. Test a known dineout-heavy place
    print("\n2. Searching 'Pop Tates' 'Mumbai'...")
    try:
        result = await service.find_restaurant_url("Pop Tates", "Mumbai")
        print(f"SEARCH RETURNED: {result}")
        url = result.get("url", "") if isinstance(result, dict) else str(result)
        if url and "swiggy.com" in url:
            print("✅ Search returned valid URL.")
        else:
            print("❌ Search failed.")
    except Exception as e:
        print(f"❌ Error: {e}")

    # 3. Test specific user request: Cheelizza Sakinaka
    print("\n3. Searching 'Cheelizza Sakinaka'...")
    try:
        result = await service.find_restaurant_url("Cheelizza", "Sakinaka")
        print(f"SEARCH RETURNED: {result}")
        url = result.get("url", "") if isinstance(result, dict) else str(result)
        expected_part = "cheelizza-india-ka-pizza-sakinaka"
        if url and expected_part in url:
            print("✅ SUCCESS: Found URL for Cheelizza Sakinaka.")
        else:
            print(f"❌ FAILURE: Expected match for '{expected_part}'.")
    except Exception as e:
        print(f"❌ Error: {e}")

    # 4. Test User Request: Nav Mejwani, dadar west
    print("\n4. Searching 'Nav Mejwani', 'Dadar West'...")
    try:
        result = await service.find_restaurant_url("Nav Mejwani", "Dadar West")
        print(f"SEARCH RETURNED: {result}")

        # Handle dict response
        url = ""
        if isinstance(result, dict):
            url = result.get("url", "")
            if result.get("dineout_only"):
                print("Note: Result is Dineout Only")
        else:
            url = str(result)

        # Validating if we got a swiggy link
        if url and "swiggy.com" in url:
            print(f"✅ SUCCESS: Found URL for Nav Mejwani: {url}")
        else:
            print(
                f"❌ FAILURE: Could not find URL for Nav Mejwani. Result was: {result}"
            )
    except Exception as e:
        print(f"❌ Error: {e}")

    # 5. Test User Request: Ishaara, Kurla
    print("\n5. Searching 'Ishaara', 'Kurla'...")
    try:
        result = await service.find_restaurant_url("Ishaara", "Kurla")
        print(f"SEARCH RETURNED: {result}")

        url = ""
        if isinstance(result, dict):
            url = result.get("url", "")
        else:
            url = str(result)

        if url and "swiggy.com" in url:
            print(f"✅ SUCCESS: Found URL for Ishaara: {url}")
        else:
            print(f"❌ FAILURE: Could not find URL for Ishaara. Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(verify_search())
