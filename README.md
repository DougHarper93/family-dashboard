# Harper Family Dashboard

A self-hosted family management web app. One screen to handle upcoming events, bills, weekly meal plans, and shopping list notifications.

## Features

- **Events** — add and track upcoming events per family member with type tags (appointment, sport, school, etc.) and a per-member calendar view
- **Bills** — track recurring and one-off bills with due dates, amounts, and paid/unpaid status
- **Meal planning** — AI-generated weekly dinner plan (Mon–Fri) with recipe images and links, individual day re-roll, and automated shopping list
- **Shopping list** — sends the week's ingredients to your phone via push notification (ntfy.sh)
- **Push notifications** — 1-day and 3-day advance reminders for upcoming events and bills via APScheduler, delivered to ntfy.sh
- **Dark mode** — system preference detection with manual toggle

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | PostgreSQL 16 |
| Notifications | ntfy.sh |
| AI | Claude (Anthropic) — meal planning and shopping list |
| Infrastructure | Docker Compose |

## Project Structure

```
family-dashboard/
├── api/                    # FastAPI backend
│   ├── main.py             # App setup, APScheduler for notifications
│   ├── database.py         # SQLAlchemy setup
│   ├── models.py           # DB models
│   ├── routers/
│   │   ├── events.py       # CRUD + upcoming events
│   │   ├── bills.py        # CRUD + paid/unpaid toggle
│   │   ├── meals.py        # Meal plan generation, re-roll, shopping list
│   │   └── notifications.py# Push notification logic
│   └── Dockerfile
├── scraper/                # Recipe scraper — run once to populate recipes.db
│   ├── scrape.py           # Entry point: python scrape.py
│   ├── database.py         # SQLite schema + helpers
│   ├── requirements.txt
│   └── scrapers/
│       ├── andy_cooks.py   # andy-cooks.com (dinner tag pages)
│       └── recipe_tin_eats.py # recipetineats.com (sitemap)
├── web/                    # Next.js frontend
│   ├── app/
│   │   ├── page.tsx        # Main dashboard (events, bills, meals)
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── CalendarView.tsx
│   │   ├── AddEventModal.tsx
│   │   ├── AddBillModal.tsx
│   │   └── ThemeProvider.tsx
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Setup

### 1. Clone and configure

```bash
git clone git@github.com:DougHarper93/family-dashboard.git
cd family-dashboard
cp .env.example .env
# Edit .env with your values
```

### 2. Populate the recipe database

The meal planner draws recipes from a local SQLite database. You need to run the scraper once before starting the app:

```bash
cd scraper
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scrape.py             # scrape all sources (~30 mins, ~800 recipes)
python scrape.py --limit 50  # quick test run (50 recipes per source)
python scrape.py --andy      # Andy Cooks only
python scrape.py --rte       # RecipeTin Eats only
```

This creates `scraper/recipes.db` which Docker mounts into the API container. You only need to run it once — re-run periodically to pick up new recipes.

### 3. Start everything

```bash
docker compose up -d
# Web: http://localhost:3003
# API: http://localhost:8002
```

The database schema is created automatically on first startup.

## Notifications

Push notifications are sent via [ntfy.sh](https://ntfy.sh) — a free, open-source push notification service. Subscribe to your topic in the ntfy app on your phone to receive alerts.

Scheduled reminders run daily at 8am and notify for:
- Events happening **today** or **tomorrow**
- Bills **due today** or **overdue**

Shopping list notifications are sent on demand from the dashboard via the **Send Shopping List** button.

To test notifications without waiting for the scheduler, exec into the API container:

```bash
docker exec -it family-api python3 -c "
import asyncio
from api.routers.notifications import check_and_send_notifications
asyncio.run(check_and_send_notifications())
"
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|----------|-------------|
| `DB_NAME` | PostgreSQL database name |
| `DB_USER` | PostgreSQL user |
| `DB_PASS` | PostgreSQL password |
| `NTFY_TOPIC` | Full ntfy.sh topic URL (e.g. `https://ntfy.sh/yourfamily-abc123`) |
| `ANTHROPIC_API_KEY` | Claude API key for meal planning and shopping list generation |
