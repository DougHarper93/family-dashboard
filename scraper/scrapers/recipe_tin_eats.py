"""
Scraper for recipetineats.com
Uses the WordPress sitemap to get all recipe URLs, then extracts schema.org data.
"""
import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from scrapers.base import fetch, extract_schema_recipe, is_seafood_recipe, get_image_url, classify_main_meal
from database import upsert_recipe

SITEMAP_INDEX = "https://www.recipetineats.com/sitemap_index.xml"
BASE_URL = "https://www.recipetineats.com"


def get_recipe_urls():
    """Fetch all recipe post URLs from WordPress sitemap."""
    urls = []
    try:
        resp = fetch(SITEMAP_INDEX, delay=0.5)
        root = ET.fromstring(resp.text)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # WordPress sitemap index lists sub-sitemaps
        for loc in root.findall(".//sm:loc", ns):
            sitemap_url = loc.text
            # Post sitemaps contain recipes; skip page/category sitemaps
            if "post-sitemap" in sitemap_url:
                try:
                    sub_resp = fetch(sitemap_url, delay=0.8)
                    sub_root = ET.fromstring(sub_resp.text)
                    for sub_loc in sub_root.findall(".//sm:loc", ns):
                        url = sub_loc.text
                        # Recipes are top-level paths (not /category/ or /tag/)
                        path = url.replace(BASE_URL, "").strip("/")
                        if path and "/" not in path:
                            urls.append(url)
                    print(f"[recipe-tin-eats] Loaded sitemap: {sitemap_url} ({len(urls)} urls so far)")
                except Exception as e:
                    print(f"[recipe-tin-eats] Sub-sitemap error {sitemap_url}: {e}")
    except Exception as e:
        print(f"[recipe-tin-eats] Sitemap index error: {e}")

    return list(set(urls))


def scrape_recipe(url):
    """Scrape a single recipe page."""
    try:
        resp = fetch(url, delay=1.2)
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
            "source": "RecipeTin Eats",
            "image_url": image_url,
            "ingredients": ingredients,
            "category": category,
            "is_seafood": is_seafood_recipe(title, ingredients),
            "is_main_meal": classify_main_meal(title, category),
        }
    except Exception as e:
        print(f"[recipe-tin-eats] Error scraping {url}: {e}")
        return None


def run(limit=None):
    """Main scraper entry point."""
    print("[recipe-tin-eats] Fetching recipe URLs from sitemap...")
    urls = get_recipe_urls()
    print(f"[recipe-tin-eats] Found {len(urls)} candidate URLs")

    if limit:
        urls = urls[:limit]

    saved = 0
    for i, url in enumerate(urls, 1):
        print(f"[recipe-tin-eats] {i}/{len(urls)} {url}")
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

    print(f"[recipe-tin-eats] Done. Saved {saved} recipes.")
    return saved
