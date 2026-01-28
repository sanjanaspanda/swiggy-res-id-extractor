# Swiggy Data Extractor API Documentation

This API allows you to search for Swiggy restaurant URLs and extract detailed information (promo codes, 99 store items, ratings) from them using a stealthy, anti-detection browser service.

## Base URL

```
http://localhost:8000
```

## Endpoints

### 1. Search Restaurant URL

Search for a restaurant's Swiggy page URL by name and location.

- **URL**: `/api/v1/search`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### Request Body

| Field | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `name` | `string` | Name of the restaurant | Yes |
| `location` | `string` | Location/City of the restaurant | Yes |

**Example Request:**

```json
{
  "name": "Pizza Hut",
  "location": "Mumbai"
}
```

#### Response

- **Status: 200 OK**

**Example Response:**

```json
{
  "url": "https://www.swiggy.com/restaurants/pizza-hut-lower-parel-mumbai-714"
}
```

- **Status: 404 Not Found**
    - Body: `{"detail": "Restaurant not found"}`

---

### 2. Extract Restaurant Data

Extract promo codes, "99 Store" items, and rating information from a specific Swiggy restaurant URL.

- **URL**: `/api/v1/extract`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### Request Body

| Field | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `url` | `string` | Valid Swiggy restaurant URL | Yes |

**Example Request:**

```json
{
  "url": "https://www.swiggy.com/restaurants/pizza-hut-lower-parel-mumbai-714"
}
```

#### Response

- **Status: 200 OK**

**Example Response:**

```json
{
  "promo_codes": [
    "50% OFF | USE SWIGGY50",
    "FLAT ₹125 OFF | USE MATCHDAY"
  ],
  "items_99": [
    "Veg Pizza",
    "Cheese Garlic Bread"
  ],
  "rating": "4.1",
  "total_ratings": "5K+ ratings"
}
```

- **Status: 400 Bad Request**
    - If the URL is invalid or an extraction error occurs.

## Notes

- The extraction service uses a headless browser with anti-bot detection measures.
- Responses may take a few seconds to generate as the browser navigates the page in real-time.
