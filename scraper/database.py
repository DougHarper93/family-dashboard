import sqlite3
import os

DB_PATH = os.environ.get("RECIPES_DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "recipes.db"))


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS recipes (
            id            INTEGER PRIMARY KEY,
            title         TEXT NOT NULL,
            url           TEXT UNIQUE NOT NULL,
            source        TEXT NOT NULL,
            image_url     TEXT,
            ingredients   TEXT,   -- JSON array of strings
            category      TEXT,   -- schema.org recipeCategory
            is_seafood    INTEGER DEFAULT 0,
            is_main_meal  INTEGER DEFAULT 0,
            scraped_at    TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS weekly_plans (
            id           INTEGER PRIMARY KEY,
            week_start   TEXT NOT NULL,
            monday_id    INTEGER REFERENCES recipes(id),
            tuesday_id   INTEGER REFERENCES recipes(id),
            wednesday_id INTEGER REFERENCES recipes(id),
            thursday_id  INTEGER REFERENCES recipes(id),
            friday_id    INTEGER REFERENCES recipes(id),
            created_at   TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


def upsert_recipe(title, url, source, image_url, ingredients, is_seafood,
                  category=None, is_main_meal=False):
    conn = get_conn()
    # Add missing columns if DB was created before this migration
    existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(recipes)")}
    if "category" not in existing_cols:
        conn.execute("ALTER TABLE recipes ADD COLUMN category TEXT")
    if "is_main_meal" not in existing_cols:
        conn.execute("ALTER TABLE recipes ADD COLUMN is_main_meal INTEGER DEFAULT 0")
    conn.commit()

    conn.execute("""
        INSERT INTO recipes (title, url, source, image_url, ingredients,
                             category, is_seafood, is_main_meal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            title        = excluded.title,
            image_url    = excluded.image_url,
            ingredients  = excluded.ingredients,
            category     = excluded.category,
            is_seafood   = excluded.is_seafood,
            is_main_meal = excluded.is_main_meal,
            scraped_at   = datetime('now')
    """, (title, url, source, image_url, ingredients,
          category, int(is_seafood), int(is_main_meal)))
    conn.commit()
    conn.close()


def get_all_recipes():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM recipes").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recipe_count():
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
    conn.close()
    return n


def get_current_week_plan():
    from datetime import date, timedelta
    today = date.today()
    saturday = today - timedelta(days=(today.weekday() + 2) % 7)
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM weekly_plans WHERE week_start = ? ORDER BY created_at DESC LIMIT 1",
        (saturday.isoformat(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_week_plan(week_start, recipe_ids):
    """recipe_ids: list of 5 ids [mon, tue, wed, thu, fri]"""
    conn = get_conn()
    conn.execute("""
        INSERT INTO weekly_plans (week_start, monday_id, tuesday_id, wednesday_id, thursday_id, friday_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (week_start, *recipe_ids))
    conn.commit()
    conn.close()


def update_week_plan_day(plan_id, day, recipe_id):
    col = f"{day}_id"
    conn = get_conn()
    conn.execute(f"UPDATE weekly_plans SET {col} = ? WHERE id = ?", (recipe_id, plan_id))
    conn.commit()
    conn.close()


def get_recipe_by_id(recipe_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_recently_used_ids(weeks=3):
    conn = get_conn()
    rows = conn.execute(
        "SELECT monday_id, tuesday_id, wednesday_id, thursday_id, friday_id "
        "FROM weekly_plans ORDER BY created_at DESC LIMIT ?",
        (weeks,)
    ).fetchall()
    conn.close()
    ids = set()
    for row in rows:
        ids.update(v for v in row if v is not None)
    return ids
