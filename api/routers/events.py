from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from database import get_db

router = APIRouter(prefix="/events", tags=["events"])


class EventCreate(BaseModel):
    title: str
    date: str
    time: Optional[str] = None
    type: str = "appointment"
    notes: Optional[str] = None
    family_member: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    type: Optional[str] = None
    notes: Optional[str] = None
    family_member: Optional[str] = None


@router.get("")
def list_events(member: Optional[str] = None, db: Session = Depends(get_db)):
    if member:
        rows = db.execute(text(
            "SELECT * FROM events WHERE family_member = :member ORDER BY date ASC, time ASC NULLS LAST"
        ), {"member": member}).fetchall()
    else:
        rows = db.execute(text(
            "SELECT * FROM events ORDER BY date ASC, time ASC NULLS LAST"
        )).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/upcoming")
def upcoming_events(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT * FROM events WHERE date >= CURRENT_DATE "
        "ORDER BY date ASC, time ASC NULLS LAST"
    )).fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("")
def create_event(body: EventCreate, db: Session = Depends(get_db)):
    row = db.execute(text(
        "INSERT INTO events (title, date, time, type, notes, family_member) "
        "VALUES (:title, :date, :time, :type, :notes, :family_member) RETURNING *"
    ), body.model_dump()).fetchone()
    db.commit()
    return dict(row._mapping)


@router.patch("/{event_id}")
def update_event(event_id: int, body: EventUpdate, db: Session = Depends(get_db)):
    existing = db.execute(text("SELECT * FROM events WHERE id = :id"), {"id": event_id}).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Event not found")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        return dict(existing._mapping)
    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["id"] = event_id
    row = db.execute(text(f"UPDATE events SET {set_clause} WHERE id = :id RETURNING *"), updates).fetchone()
    db.commit()
    return dict(row._mapping)


@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    result = db.execute(text("DELETE FROM events WHERE id = :id"), {"id": event_id})
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"ok": True}
