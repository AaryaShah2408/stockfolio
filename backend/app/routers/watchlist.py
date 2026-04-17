from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.auth import get_current_user
from app import models, schemas

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

@router.get("/", response_model=List[schemas.WatchlistOut])
def get_watchlist(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(models.Watchlist).filter(models.Watchlist.user_id == current_user.id).all()

@router.post("/", response_model=schemas.WatchlistOut, status_code=201)
def add_to_watchlist(data: schemas.WatchlistCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    existing = db.query(models.Watchlist).filter(
        models.Watchlist.user_id == current_user.id,
        models.Watchlist.stock_id == data.stock_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Stock already in watchlist")
    stock = db.query(models.Stock).filter(models.Stock.id == data.stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    item = models.Watchlist(user_id=current_user.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{watchlist_id}", status_code=204)
def remove_from_watchlist(watchlist_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = db.query(models.Watchlist).filter(
        models.Watchlist.id == watchlist_id,
        models.Watchlist.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    db.delete(item)
    db.commit()
