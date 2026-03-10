"""
Scrapes recipes from all sources and saves them to the database.
Run this once to populate, then periodically to pick up new recipes.

Usage:
  python scrape.py              # scrape all sources
  python scrape.py --andy       # andy-cooks.com only
  python scrape.py --rte        # recipetineats.com only
  python scrape.py --limit 20   # limit per source (useful for testing)
"""
import argparse
from database import init_db, get_recipe_count

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--andy",  action="store_true", help="Scrape Andy Cooks only")
    parser.add_argument("--rte",   action="store_true", help="Scrape RecipeTin Eats only")
    parser.add_argument("--limit", type=int, default=None, help="Max recipes per source")
    args = parser.parse_args()

    init_db()

    run_all = not args.andy and not args.rte

    if args.andy or run_all:
        from scrapers.andy_cooks import run as run_andy
        run_andy(limit=args.limit)

    if args.rte or run_all:
        from scrapers.recipe_tin_eats import run as run_rte
        run_rte(limit=args.limit)

    print(f"\n✅ Total recipes in DB: {get_recipe_count()}")

if __name__ == "__main__":
    main()
