from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.auth import get_current_user
from app import models, schemas

router = APIRouter(prefix="/stocks", tags=["Stocks"])

@router.get("/", response_model=List[schemas.StockOut])
def list_stocks(
    sector: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(models.Stock)
    if sector:
        q = q.filter(models.Stock.sector == sector)
    if search:
        q = q.filter(
            models.Stock.ticker.ilike(f"%{search}%") |
            models.Stock.company_name.ilike(f"%{search}%")
        )
    return q.offset(skip).limit(limit).all()

@router.get("/sectors", response_model=List[str])
def list_sectors(db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = db.query(models.Stock.sector).distinct().all()
    return [r[0] for r in rows]

@router.get("/{stock_id}", response_model=schemas.StockOut)
def get_stock(stock_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock

@router.patch("/{stock_id}", response_model=schemas.StockOut)
def update_stock(stock_id: int, data: schemas.StockUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(stock, field, value)
    db.commit()
    db.refresh(stock)
    return stock

@router.get("/{stock_id}/history", response_model=List[schemas.PriceHistoryOut])
def get_price_history(
    stock_id: int,
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(days=days)
    history = (
        db.query(models.PriceHistory)
        .filter(models.PriceHistory.stock_id == stock_id, models.PriceHistory.date >= since)
        .order_by(models.PriceHistory.date)
        .all()
    )
    return history
