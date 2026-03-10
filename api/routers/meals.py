import sqlite3
import json
import os
import random
import urllib.request
from datetime import date, timedelta
from fastapi import APIRouter, HTTPException
import anthropic

router = APIRouter(prefix="/meals", tags=["meals"])

SQLITE_PATH = os.environ.get("MEAL_DB_PATH", "/app/data/recipes.db")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

VALID_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"]


def get_meal_db():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def current_saturday():
    today = date.today()
    return today - timedelta(days=(today.weekday() + 2) % 7)


def fetch_current_plan(conn):
    saturday = current_saturday()
    row = conn.execute(
        "SELECT * FROM weekly_plans WHERE week_start = ? ORDER BY created_at DESC LIMIT 1",
        (saturday.isoformat(),)
    ).fetchone()
    if not row:
        row = conn.execute(
            "SELECT * FROM weekly_plans ORDER BY week_start DESC, created_at DESC LIMIT 1"
        ).fetchone()
    return dict(row) if row else None


def build_ai_shopping_list(recipes: list, meal_lines: list) -> str:
    """Send raw recipe ingredients to Claude and get back a clean shopping list."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Build the raw ingredient dump for Claude
    recipe_blocks = []
    for i, recipe in enumerate(recipes):
        raw = recipe.get("ingredients", "[]")
        try:
            ingredients = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            ingredients = []

        # Clean HTML entities from ingredient strings
        cleaned = [
            ing.replace("&quot;", '"').replace("&amp;", "&").replace("&#39;", "'")
            for ing in ingredients
        ]
        recipe_blocks.append(f"Recipe: {recipe['title']}\n" + "\n".join(f"  - {ing}" for ing in cleaned))

    raw_ingredients = "\n\n".join(recipe_blocks)

    prompt = f"""You are helping an Australian family compile their weekly grocery shopping list.

Here are the raw ingredient lists from this week's {len(recipes)} dinner recipes:

{raw_ingredients}

Please produce a clean, consolidated shopping list following these rules:
- Combine the same ingredient from multiple recipes and add the quantities together (e.g. 500g chicken from one recipe + 400g chicken from another = 900g chicken)
- Use Australian metric units (g, kg, ml, L). Convert imperial to metric where needed
- Strip out cooking instructions, notes in brackets, and qualifiers like "roughly chopped" or "boneless skinless" — just the ingredient and quantity
- Round quantities to sensible numbers (e.g. 450g → 500g, 0.9kg → 1kg)
- Group items under these headings: Meat & Protein, Seafood, Fruit & Veg, Dairy & Eggs, Pantry & Dry Goods, Herbs & Spices
- Only include headings that have items
- Format each item as a simple bullet: - Chicken thighs 1kg
- Do not include seasonings like salt, pepper, or water
- Keep it short and practical — this goes straight to a phone as a push notification
- Plain text only, no markdown formatting"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text.strip()


@router.get("/current-week")
def current_week():
    if not os.path.exists(SQLITE_PATH):
        raise HTTPException(status_code=503, detail="Meal planner database not available")
    conn = get_meal_db()
    try:
        plan = fetch_current_plan(conn)
        if not plan:
            return {"week_start": None, "meals": None}

        meals = {}
        for day in VALID_DAYS:
            recipe_id = plan.get(f"{day}_id")
            if recipe_id:
                row = conn.execute(
                    "SELECT id, title, url, image_url, category FROM recipes WHERE id = ?",
                    (recipe_id,)
                ).fetchone()
                meals[day] = dict(row) if row else None
            else:
                meals[day] = None

        return {"week_start": plan["week_start"], "meals": meals}
    finally:
        conn.close()


@router.post("/reroll/{day}")
def reroll_day(day: str):
    if day not in VALID_DAYS:
        raise HTTPException(status_code=400, detail=f"Invalid day. Must be one of: {', '.join(VALID_DAYS)}")
    if not os.path.exists(SQLITE_PATH):
        raise HTTPException(status_code=503, detail="Meal planner database not available")

    conn = get_meal_db()
    try:
        plan = fetch_current_plan(conn)
        if not plan:
            raise HTTPException(status_code=404, detail="No meal plan for this week")

        recent_rows = conn.execute(
            "SELECT monday_id, tuesday_id, wednesday_id, thursday_id, friday_id "
            "FROM weekly_plans ORDER BY created_at DESC LIMIT 2"
        ).fetchall()
        recently_used = set()
        for row in recent_rows:
            recently_used.update(v for v in row if v is not None)

        current_ids = {plan[f"{d}_id"] for d in VALID_DAYS if d != day and plan.get(f"{d}_id")}
        exclude_ids = current_ids | recently_used

        all_recipes = conn.execute(
            "SELECT id, title, url, image_url, category, ingredients FROM recipes WHERE is_main_meal = 1"
        ).fetchall()
        all_recipes = [dict(r) for r in all_recipes]

        candidates = [r for r in all_recipes if r["id"] not in exclude_ids]
        if not candidates:
            candidates = all_recipes

        new_recipe = random.choice(candidates)

        conn.execute(
            f"UPDATE weekly_plans SET {day}_id = ? WHERE id = ?",
            (new_recipe["id"], plan["id"])
        )
        conn.commit()

        return {
            "id": new_recipe["id"],
            "title": new_recipe["title"],
            "url": new_recipe["url"],
            "image_url": new_recipe["image_url"],
            "category": new_recipe["category"],
        }
    finally:
        conn.close()


@router.post("/send-shopping-list")
def send_shopping_list():
    if not NTFY_TOPIC:
        raise HTTPException(status_code=503, detail="NTFY_TOPIC not configured")
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")
    if not os.path.exists(SQLITE_PATH):
        raise HTTPException(status_code=503, detail="Meal planner database not available")

    conn = get_meal_db()
    try:
        plan = fetch_current_plan(conn)
        if not plan:
            raise HTTPException(status_code=404, detail="No meal plan for this week")

        recipes = []
        meal_lines = []
        day_labels = {"monday": "Mon", "tuesday": "Tue", "wednesday": "Wed", "thursday": "Thu", "friday": "Fri"}
        for day in VALID_DAYS:
            recipe_id = plan.get(f"{day}_id")
            if recipe_id:
                row = conn.execute(
                    "SELECT id, title, url, image_url, category, ingredients FROM recipes WHERE id = ?",
                    (recipe_id,)
                ).fetchone()
                if row:
                    r = dict(row)
                    recipes.append(r)
                    meal_lines.append(f"{day_labels[day]}: {r['title']}")

        # Ask Claude to build the shopping list
        shopping_list = build_ai_shopping_list(recipes, meal_lines)

        saturday = current_saturday()
        week_str = saturday.strftime("%-d %b %Y")

        message = f"Shopping List - Week of {week_str}\n\n"
        message += "\n".join(meal_lines)
        message += f"\n\n{shopping_list}"

        # Trim to ntfy's 4096 byte limit if needed
        encoded = message.encode("utf-8")
        if len(encoded) > 4000:
            message = encoded[:4000].decode("utf-8", errors="ignore") + "\n..."

        req = urllib.request.Request(
            NTFY_TOPIC,
            data=message.encode("utf-8"),
            headers={
                "Content-Type": "text/plain; charset=utf-8",
                "Title": f"Shopping List - Week of {week_str}",
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
        return {"ok": True}
    finally:
        conn.close()
