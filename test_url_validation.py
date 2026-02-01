import re


def validate_url(url):
    pattern = r"-(?:rest)?\d+$"
    # Basic cleanup to match what happens in the service (stripping trailing slash)
    cleaned_url = url.rstrip("/")
    if re.search(pattern, cleaned_url):
        return True
    return False


def test_urls():
    test_cases = [
        ("https://www.swiggy.com/restaurants/pizza-hut-colaba-mumbai-123456", True),
        (
            "https://www.swiggy.com/restaurants/burger-king-churchgate-mumbai-rest12345",
            True,
        ),
        ("https://www.swiggy.com/restaurants/some-place-rest555", True),
        ("https://www.swiggy.com/restaurants/just-digits-99999", True),
        ("https://www.swiggy.com/city/mumbai", False),
        ("https://www.swiggy.com/restaurants/pizza-hut-colaba-mumbai", False),
        ("https://www.swiggy.com/restaurants/bad-url-rest", False),
        ("https://www.swiggy.com/restaurants/another-bad-url-123-abc", False),
        ("https://www.swiggy.com/restaurants/valid-url-12345/", True),  # Trailing slash
    ]

    print("Running Regex Validation Tests...")
    all_passed = True
    for url, expected in test_cases:
        result = validate_url(url)
        if result == expected:
            print(f"✅ PASS: {url} -> {result}")
        else:
            print(f"❌ FAIL: {url} -> Got {result}, Expected {expected}")
            all_passed = False

    if all_passed:
        print("\nAll tests passed successfully!")
    else:
        print("\nSome tests failed.")


if __name__ == "__main__":
    test_urls()
