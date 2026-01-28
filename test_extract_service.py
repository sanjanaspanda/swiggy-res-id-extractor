import asyncio
from app.services.extract_service import SwiggyExtractService

# Sample data provided by the user
sample_response = {
    "statusCode": 0,
    "data": {
        "statusMessage": "done successfully",
        "cards": [
            {
                "card": {
                    "card": {
                        "@type": "type.googleapis.com/swiggy.presentation.food.v2.Restaurant",
                        "info": {
                            "id": "20170",
                            "name": "The Plush",
                            "avgRatingString": "4.4",
                            "totalRatingsString": "15K+ ratings",
                        },
                    }
                }
            }
        ],
    },
}


async def test_service_extraction():
    print("Testing SwiggyExtractService.extract_ratings...")
    service = SwiggyExtractService()

    # Test the standalone method
    result = service.extract_ratings(sample_response["data"])
    print(f"Extraction Result: {result}")

    expected = {"avgRatingString": "4.4", "totalRatingsString": "15K+ ratings"}

    if result == expected:
        print("✅ SUCCESS: Service extraction matched expected values.")
    else:
        print(f"❌ FAILURE: Expected {expected}, got {result}")


async def test_offer_extraction():
    print("\nTesting SwiggyExtractService.extract_offer_items...")
    service = SwiggyExtractService()

    # Snippet from user
    offer_card = {
        "card": {
            "@type": "type.googleapis.com/swiggy.presentation.food.v2.Dish",
            "info": {
                "id": "191719801",
                "name": "Korean Mushroom Peppers Pizza_50%",
                "category": "Pizzas_Flat 50% Off",  # Keyword matched
                "offerTags": [
                    {
                        "title": "50% OFF",  # Tag matched
                        "textColor": "#DB6742",
                        "backgroundColor": "#FAE8E3",
                        "matchText": "SILD",
                    }
                ],
                "inStock": 1,
            },
        }
    }

    # Wrap in expected structure if needed, or recursive handles it given root is dict.
    # The method takes `response_data`.

    result = service.extract_offer_items(offer_card)
    print(f"Offer Extraction Result: {result}")

    # We expect mapped by both category AND offer tag if they exist.
    # Category: "Pizzas_Flat 50% Off" -> ["Korean Mushroom Peppers Pizza_50%"]
    # OfferTag: "50% OFF" -> ["Korean Mushroom Peppers Pizza_50%"]

    expected_contains_cat = "Pizzas_Flat 50% Off" in result
    expected_contains_tag = "50% OFF" in result

    if expected_contains_cat and expected_contains_tag:
        print("✅ SUCCESS: Offer extraction found both category and tag based offers.")
    elif expected_contains_cat:
        print("⚠️ PARTIAL: Found category match but not tag.")
    elif expected_contains_tag:
        print("⚠️ PARTIAL: Found tag match but not category.")
    else:
        print("❌ FAILURE: Did not find expected offers.")


if __name__ == "__main__":
    asyncio.run(test_service_extraction())
    asyncio.run(test_offer_extraction())
