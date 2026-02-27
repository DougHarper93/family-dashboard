from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from database import get_db

router = APIRouter(prefix="/bills", tags=["bills"])


class BillCreate(BaseModel):
    name: str
    amount: Optional[float] = None
    due_date: str
    category: str = "other"
    recurring: bool = False


class BillUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    due_date: Optional[str] = None
    category: Optional[str] = None
    recurring: Optional[bool] = None
    paid: Optional[bool] = None


@router.get("")
def list_bills(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT * FROM bills ORDER BY paid ASC, due_date ASC"
    )).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/upcoming")
def upcoming_bills(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT * FROM bills WHERE paid = FALSE AND due_date >= CURRENT_DATE "
        "ORDER BY due_date ASC LIMIT 10"
    )).fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("")
def create_bill(body: BillCreate, db: Session = Depends(get_db)):
    row = db.execute(text(
        "INSERT INTO bills (name, amount, due_date, category, recurring) "
        "VALUES (:name, :amount, :due_date, :category, :recurring) RETURNING *"
    ), body.model_dump()).fetchone()
    db.commit()
    return dict(row._mapping)


@router.patch("/{bill_id}/toggle")
def toggle_paid(bill_id: int, db: Session = Depends(get_db)):
    row = db.execute(text(
        "UPDATE bills SET paid = NOT paid WHERE id = :id RETURNING *"
    ), {"id": bill_id}).fetchone()
    db.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Bill not found")
    return dict(row._mapping)


@router.patch("/{bill_id}")
def update_bill(bill_id: int, body: BillUpdate, db: Session = Depends(get_db)):
    existing = db.execute(text("SELECT * FROM bills WHERE id = :id"), {"id": bill_id}).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Bill not found")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        return dict(existing._mapping)
    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["id"] = bill_id
    row = db.execute(text(f"UPDATE bills SET {set_clause} WHERE id = :id RETURNING *"), updates).fetchone()
    db.commit()
    return dict(row._mapping)


@router.delete("/{bill_id}")
def delete_bill(bill_id: int, db: Session = Depends(get_db)):
    result = db.execute(text("DELETE FROM bills WHERE id = :id"), {"id": bill_id})
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Bill not found")
    return {"ok": True}
