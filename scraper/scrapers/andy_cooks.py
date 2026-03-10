"""
Scraper for andy-cooks.com
Uses the /tagged/dinner/ pages to get only dinner recipe URLs,
then extracts schema.org data. This is more reliable than keyword
classification since it uses Andy's own categorisation.
"""
import json
from bs4 import BeautifulSoup
from scrapers.base import fetch, extract_schema_recipe, is_seafood_recipe, get_image_url
from database import upsert_recipe

BASE_URL = "https://www.andy-cooks.com"
DINNER_TAG_URL = f"{BASE_URL}/blogs/recipes/tagged/dinner"


def get_recipe_urls():
    """Fetch dinner recipe URLs from /tagged/dinner/ paginated pages."""
    urls = set()
    page = 1
    while True:
        try:
            url = f"{DINNER_TAG_URL}?page={page}"
            resp = fetch(url, delay=0.8)
            soup = BeautifulSoup(resp.text, "lxml")
            links = soup.select("a[href*='/blogs/recipes/']")
            recipe_links = [
                a["href"] for a in links
                if a["href"].startswith("/blogs/recipes/")
                and "/tagged/" not in a["href"]
                and "?" not in a["href"]
                and a["href"] != "/blogs/recipes"
            ]
            if not recipe_links:
                break
            urls.update(recipe_links)
            print(f"[andy-cooks] Tagged page {page}: {len(recipe_links)} recipes (total: {len(urls)})")
            page += 1
            if page > 100:  # safety cap
                break
        except Exception as e:
            print(f"[andy-cooks] Tag page {page} error: {e}")
            break

    return [BASE_URL + path for path in urls]


def scrape_recipe(url):
    """Scrape a single recipe page."""
    try:
        resp = fetch(url, delay=1.0)
        soup = BeautifulSoup(resp.text, "lxml")
        schema = extract_schema_recipe(soup)
        if not schema:
            return None

        title = schema.get("name", "").strip()
        ingredients = schema.get("recipeIngredient", [])
        image_url = get_image_url(schema)
        category = schema.get("recipeCategory", "")
        if isinstance(category, list):
            category = ", ".join(category)

        if not title or not ingredients:
            return None

        return {
            "title": title,
            "url": url,
            "source": "Andy Cooks",
            "image_url": image_url,
            "ingredients": ingredients,
            "category": category,
            "is_seafood": is_seafood_recipe(title, ingredients),
            # All recipes from /tagged/dinner/ are dinner recipes by definition
            "is_main_meal": True,
        }
    except Exception as e:
        print(f"[andy-cooks] Error scraping {url}: {e}")
        return None


def run(limit=None):
    """Main scraper entry point."""
    print("[andy-cooks] Fetching dinner recipe URLs from /tagged/dinner/...")
    urls = get_recipe_urls()
    print(f"[andy-cooks] Found {len(urls)} dinner recipe URLs")

    if limit:
        urls = urls[:limit]

    saved = 0
    for i, url in enumerate(urls, 1):
        print(f"[andy-cooks] {i}/{len(urls)} {url}")
        recipe = scrape_recipe(url)
        if recipe:
            upsert_recipe(
                recipe["title"],
                recipe["url"],
                recipe["source"],
                recipe["image_url"],
                json.dumps(recipe["ingredients"]),
                recipe["is_seafood"],
                category=recipe["category"],
                is_main_meal=recipe["is_main_meal"],
            )
            saved += 1

    print(f"[andy-cooks] Done. Saved {saved} recipes.")
    return saved
