
# Swiggy Restaurant ID Extractor

This script automates the process of finding Swiggy restaurant URLs for a list of restaurants. It uses **Playwright** to perform Google searches with stealth techniques to avoid CAPTCHA and handles location popups automatically.

## Prerequisites

-   Python 3.8+
-   `uv` package manager (recommended) or `pip`

## Setup Steps

Follow these steps to set up the project environment:

### 1. Install Dependencies

Install the required Python packages, including Playwright.

**Using uv (Recommended):**
```bash
uv sync
```
*Note: If you don't have `uv` installed, you can install the dependencies manually:*
```bash
pip install playwright
```

### 2. Install Playwright Browsers

You must install the Chromium browser binary for Playwright to work.

```bash
# If using uv:
uv run playwright install chromium

# If using standard python/pip:
python -m playwright install chromium
```

## How to Run

1.  **Prepare Input Data**: Ensure you have a `restaurants.csv` file in the project directory. 
    
    **Input Columns:**
    -   `Red_id`
    -   `Zomato Link`
    -   `Zomato Fallback Link`
    -   `Restaurant Name`
    -   `Location`


2.  **Execute the Script**:

    ```bash
    # Using uv:
    uv run main.py

    # Using standard python:
    python main.py
    ```

3.  **View Results**: The script will generate a new file named `restaurants_with_ids.csv` containing the original data plus the extracted Swiggy URLs.

    **Output Columns:**
    -   `Res_id`
    -   `Zomato Link`
    -   `Zomato Fallback Link`
    -   `Restaurant Name`
    -   `Location`
    -   `swiggy res id` (New Column)

## Data Cleanup Formula (Excel/Google Sheets)

You can use the following formula to parse the extracted Swiggy URL (assuming it is in column `F2`) and determine the status or extract the ID:

```excel
=LET(
    url, F2,
    notFound, ISNUMBER(SEARCH({"404","page not found"}, LOWER(url))),
    hasDineout, ISNUMBER(SEARCH("dineout", url)),
    afterRest, TRIM(MID(url, SEARCH("rest", url) + 4, LEN(url))),
    IF(
        notFound,
        "restaurant does not exist",
        IF(
            hasDineout,
            "dineout",
            afterRest
        )
    )
)
```

> [!NOTE]
> Ensure that `restaurants_with_ids.csv` is NOT open in Excel/Sheets when running the script, otherwise you will get a `PermissionError`.
