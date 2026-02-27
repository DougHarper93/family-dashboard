import os
import urllib.request
from datetime import date, timedelta
from database import SessionLocal
from sqlalchemy import text

NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")


def send_ntfy(title: str, body: str):
    if not NTFY_TOPIC:
        return
    req = urllib.request.Request(
        NTFY_TOPIC,
        data=body.encode("utf-8"),
        headers={
            "Content-Type": "text/plain; charset=utf-8",
            "Title": title,
        },
        method="POST",
    )
    urllib.request.urlopen(req, timeout=10)


def check_and_send_notifications():
    db = SessionLocal()
    try:
        today = date.today()
        for days_ahead in [3, 1]:
            target = today + timedelta(days=days_ahead)
            label = "in 3 days" if days_ahead == 3 else "tomorrow"
            col = f"notif_{days_ahead}d_sent"

            events = db.execute(text(
                f"SELECT * FROM events WHERE date = :target AND {col} = FALSE"
            ), {"target": target}).fetchall()
            for ev in events:
                ev = dict(ev._mapping)
                parts = [ev["title"], f"is {label}"]
                if ev.get("time"):
                    parts.append(f"at {ev['time']}")
                if ev.get("family_member"):
                    parts.append(f"[{ev['family_member']}]")
                send_ntfy(f"Reminder: {ev['title']}", " ".join(parts))
                db.execute(text(
                    f"UPDATE events SET {col} = TRUE WHERE id = :id"
                ), {"id": ev["id"]})

            bills = db.execute(text(
                f"SELECT * FROM bills WHERE due_date = :target AND paid = FALSE AND {col} = FALSE"
            ), {"target": target}).fetchall()
            for bill in bills:
                bill = dict(bill._mapping)
                parts = [bill["name"]]
                if bill.get("amount"):
                    parts.append(f"(${bill['amount']:.2f})")
                parts.append(f"is due {label}")
                send_ntfy(f"Bill Due: {bill['name']}", " ".join(parts))
                db.execute(text(
                    f"UPDATE bills SET {col} = TRUE WHERE id = :id"
                ), {"id": bill["id"]})

        db.commit()
    finally:
        db.close()
