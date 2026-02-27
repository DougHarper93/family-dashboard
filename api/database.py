import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "family_dashboard")
DB_USER = os.environ.get("DB_USER", "family_user")
DB_PASS = os.environ.get("DB_PASS", "")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                date DATE NOT NULL,
                time TIME,
                type TEXT NOT NULL DEFAULT 'appointment',
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bills (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                amount NUMERIC(10,2),
                due_date DATE NOT NULL,
                paid BOOLEAN NOT NULL DEFAULT FALSE,
                category TEXT NOT NULL DEFAULT 'other',
                recurring BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS family_member TEXT"))
        conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS notif_3d_sent BOOLEAN NOT NULL DEFAULT FALSE"))
        conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS notif_1d_sent BOOLEAN NOT NULL DEFAULT FALSE"))
        conn.execute(text("ALTER TABLE bills ADD COLUMN IF NOT EXISTS notif_3d_sent BOOLEAN NOT NULL DEFAULT FALSE"))
        conn.execute(text("ALTER TABLE bills ADD COLUMN IF NOT EXISTS notif_1d_sent BOOLEAN NOT NULL DEFAULT FALSE"))
        conn.commit()
