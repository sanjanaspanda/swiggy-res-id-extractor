from main import do_search


def test_fallback():
    restaurant = "The Bawa Kitchen"
    location = "Vile Parle West"
    print(f"Testing search for: {restaurant} in {location}")

    result_url = do_search(restaurant, location)
    print(f"Result URL: {result_url}")

    # Expected behavior: It should find a URL, likely pointing to Juhu if Vile Parle West specific link doesn't exist.
    if "swiggy.com/restaurants" in result_url:
        print("SUCCESS: Found a Swiggy restaurant link.")
    else:
        print("FAILURE: Did not find a valid Swiggy link.")


if __name__ == "__main__":
    test_fallback()
