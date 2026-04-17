from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.auth import get_current_user
from app import models, schemas

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])

@router.post("/", response_model=schemas.PortfolioOut, status_code=201)
def create_portfolio(data: schemas.PortfolioCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    portfolio = models.Portfolio(user_id=current_user.id, **data.model_dump())
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio

@router.get("/", response_model=List[schemas.PortfolioOut])
def list_portfolios(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(models.Portfolio).filter(models.Portfolio.user_id == current_user.id).all()

@router.get("/{portfolio_id}", response_model=schemas.PortfolioOut)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    p = db.query(models.Portfolio).filter(models.Portfolio.id == portfolio_id, models.Portfolio.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return p

@router.patch("/{portfolio_id}", response_model=schemas.PortfolioOut)
def update_portfolio(portfolio_id: int, data: schemas.PortfolioUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    p = db.query(models.Portfolio).filter(models.Portfolio.id == portfolio_id, models.Portfolio.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return p

@router.delete("/{portfolio_id}", status_code=204)
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    p = db.query(models.Portfolio).filter(models.Portfolio.id == portfolio_id, models.Portfolio.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db.delete(p)
    db.commit()
