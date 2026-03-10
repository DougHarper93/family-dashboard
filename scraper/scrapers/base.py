import json
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-AU,en;q=0.9",
}

# ── Main meal classification ─────────────────────────────────────────────────

# Title keywords that strongly indicate NOT a main meal.
# Note: avoid single words that often appear as "X with [word]" modifiers (e.g. sauce, glaze).
# Instead use more specific phrases or patterns.
NON_MEAL_TITLE_KEYWORDS = {
    # Desserts & sweet baking
    "cupcake", "cookie", "biscuit", "brownie", "pudding", "tart",
    "cheesecake", "crumble", "mousse", "sorbet", "ice cream", "fudge",
    "candy", "truffle", "shortbread", "meringue", "pavlova", "trifle",
    "tiramisu", "lamington", "donut", "doughnut", "churro", "baklava",
    "éclair", "profiterole", "macaron", "hot cross bun", "chelsea bun",
    "scone", "muffin", "panna cotta", "semifreddo", "affogato",
    "blondie", "traybake", "millefeuille",
    # Specific sauces / condiments — whole-title matches
    "gravy", "dipping sauce", "hot sauce", "chilli oil", "herb oil",
    "compound butter", "vinaigrette", "mayonnaise", "hollandaise",
    "béchamel", "beurre blanc", "bordelaise", "béarnaise",
    "tomato sugo", "salsa verde", "salsa roja", "tomato chutney",
    "chutney", "relish", "jam", "preserve", "marmalade",
    "gremolata", "kosho", "hummus", "guacamole", "tzatziki",
    "baba ghanoush", "baba ganoush",
    # Stocks & broths
    "stock", "broth", "bone broth", "dashi",
    # Drinks
    "smoothie", "cocktail", "mocktail", "juice", "lemonade", "milkshake",
    "frappe", "spritz", "sangria",
    # Breads (standalone — not filled/stuffed)
    "sourdough", "focaccia", "flatbread", "naan", "pita", "bread", "bun", "bagel",
    # Breakfast dishes
    "pancake", "waffle", "french toast", "porridge", "oatmeal", "eggs benedict",
    # Snacks, sides & starters
    "dip", "bruschetta", "crostini", "crackers", "cracker", "popcorn",
    "granola", "energy ball", "bliss ball",
    "bhaji", "pakora", "samosa", "arancini", "nachos", "sausage roll",
    # Salads (substantial protein salads caught by MAIN_MEAL_INDICATORS)
    "salad", "tabbouleh",
    # Standalone sauces not caught by specific keywords above
    "brown sauce", "white sauce", "cheese sauce", "red wine sauce",
    # Soups (substantial soups like pho/ramen/laksa are in MAIN_MEAL_INDICATORS)
    "soup",
}

# Schema.org recipeCategory values that mean it IS a main meal
MAIN_CATEGORIES = {
    "main course", "main dish", "dinner", "lunch", "mains", "main",
    "weeknight dinner", "weeknight meal", "entree", "entrée",
    "supper", "one pot", "one-pot",
}

# Schema.org recipeCategory values that mean it is NOT a main meal
NON_MEAL_CATEGORIES = {
    "dessert", "sweet", "sweets", "baking", "cake", "side dish", "sides",
    "sauce", "condiment", "snack", "snacks", "drink", "drinks",
    "beverage", "beverages", "cocktail", "appetizer", "appetisers",
    "starter", "starters", "spread", "dip", "breakfast", "brunch",
    "salad", "soup", "bread", "pastry",
}


MAIN_MEAL_INDICATORS = {
    "curry", "stew", "casserole", "pasta", "risotto",
    "stir fry", "stir-fry", "fried rice", "noodle", "burger", "taco",
    "burrito", "enchilada", "lasagne", "lasagna", "tagine",
    "biryani", "paella", "gratin", "frittata", "shakshuka", "ragu",
    "ragù", "bolognese", "carbonara", "schnitzel", "kiev", "katsu",
    "gyoza", "pierogi", "empanada", "congee", "pho",
    "ramen", "laksa", "rendang", "satay", "kebab", "souvlaki", "gyros",
    # Additional dish types that are clearly mains
    "moussaka", "spanakopita", "quiche", "bibimbap", "yakitori",
    "teriyaki", "adobo", "pozole", "mole", "goulash", "stroganoff",
    "pizza", "calzone", "torta", "bánh mì", "banh mi", "arepa", "manoush",
    "tikka", "masala", "korma", "vindaloo",
    "steak", "chop", "cutlet",
    "meatball", "meatloaf", "meat pie",
}

# Proteins that indicate a recipe is centred on a substantial ingredient.
# If nothing else matches and the title contains a protein, we include it.
PROTEIN_KEYWORDS = {
    # Meats
    "chicken", "beef", "lamb", "pork", "turkey", "duck", "venison",
    "wagyu", "veal", "kangaroo", "rabbit", "quail", "goat", "mutton",
    "ham", "bacon", "pancetta", "prosciutto", "chorizo", "salami",
    # Seafood (already in SEAFOOD_KEYWORDS too)
    "fish", "salmon", "tuna", "cod", "barramundi", "snapper", "trout",
    "prawn", "shrimp", "lobster", "crab", "squid", "calamari", "octopus",
    "scallop", "mussel", "oyster", "clam", "anchovy", "sardine",
    "halibut", "sea bass", "seafood", "shellfish", "mahi",
    "flathead", "whiting", "bream", "kingfish", "swordfish",
    # Generic protein descriptors
    "meat", "mince", "fillet", "sausage",
    # Plant proteins that anchor a main
    "lentil", "chickpea", "tofu", "tempeh",
    # Egg-based mains (shakshuka already caught by MAIN_MEAL_INDICATORS)
    "eggs benedict", "egg fried",
}


def classify_main_meal(title, category=None):
    """Return True if this recipe is likely a substantial main meal."""
    title_lower = title.lower()

    # Strong dish-type indicator → include regardless of other signals
    if any(kw in title_lower for kw in MAIN_MEAL_INDICATORS):
        return True

    # Check schema category — most reliable signal when present
    if category:
        cat_lower = category.lower()
        if any(c in cat_lower for c in MAIN_CATEGORIES):
            return True
        if any(c in cat_lower for c in NON_MEAL_CATEGORIES):
            return False

    # Title keyword exclusion
    if any(kw in title_lower for kw in NON_MEAL_TITLE_KEYWORDS):
        return False

    # Require a protein or main-meal indicator in the title — be conservative
    if any(kw in title_lower for kw in PROTEIN_KEYWORDS):
        return True

    # Default: exclude (avoids side dishes with no strong signal)
    return False


# ── Seafood detection ─────────────────────────────────────────────────────────
SEAFOOD_KEYWORDS = {
    "fish", "salmon", "tuna", "cod", "barramundi", "snapper", "trout",
    "prawn", "shrimp", "lobster", "crab", "squid", "calamari", "octopus",
    "scallop", "mussel", "oyster", "clam", "anchovy", "sardine", "mackerel",
    "halibut", "sea bass", "seafood", "shellfish", "mahi", "tilapia",
    "flathead", "whiting", "bream", "kingfish", "swordfish", "ling",
}


def fetch(url, delay=1.0):
    time.sleep(delay)
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp


def extract_schema_recipe(soup):
    """Extract schema.org Recipe JSON-LD from a page."""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            # Handle @graph arrays
            if isinstance(data, dict) and "@graph" in data:
                data = data["@graph"]
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") == "Recipe":
                        return item
            elif isinstance(data, dict) and data.get("@type") == "Recipe":
                return data
        except (json.JSONDecodeError, AttributeError):
            continue
    return None


def is_seafood_recipe(title, ingredients):
    text = (title + " " + " ".join(ingredients)).lower()
    return any(kw in text for kw in SEAFOOD_KEYWORDS)


def get_image_url(schema):
    img = schema.get("image")
    if isinstance(img, str):
        return img
    if isinstance(img, list) and img:
        first = img[0]
        return first.get("url", first) if isinstance(first, dict) else first
    if isinstance(img, dict):
        return img.get("url", "")
    return ""
