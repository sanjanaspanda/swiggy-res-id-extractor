import json
from get_coupon_code import extract_ratings

# Sample data provided by the user
sample_response = {
    "statusCode": 0,
    "data": {
        "statusMessage": "done successfully",
        "cards": [
            {
                "card": {
                    "card": {
                        "@type": "type.googleapis.com/swiggy.gandalf.widgets.v2.TextBoxV2",
                        "text": "The Plush",
                    }
                }
            },
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
            },
        ],
    },
}


def test_extraction():
    print("Testing extract_ratings...")
    result = extract_ratings(sample_response["data"])
    print(f"Result: {result}")

    expected = {"avgRatingString": "4.4", "totalRatingsString": "15K+ ratings"}

    if result == expected:
        print("✅ SUCCESS: Extraction matched expected values.")
    else:
        print(f"❌ FAILURE: Expected {expected}, got {result}")


if __name__ == "__main__":
    test_extraction()
