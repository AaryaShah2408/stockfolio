from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.auth import get_current_user
from app import models, schemas

router = APIRouter(prefix="/portfolios/{portfolio_id}/transactions", tags=["Transactions"])

def _get_portfolio(portfolio_id: int, current_user, db: Session):
    p = db.query(models.Portfolio).filter(
        models.Portfolio.id == portfolio_id,
        models.Portfolio.user_id == current_user.id
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return p

@router.get("/", response_model=List[schemas.TransactionOut])
def list_transactions(
    portfolio_id: int,
    stock_id: Optional[int] = Query(None),
    transaction_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _get_portfolio(portfolio_id, current_user, db)
    q = db.query(models.Transaction).filter(models.Transaction.portfolio_id == portfolio_id)
    if stock_id:
        q = q.filter(models.Transaction.stock_id == stock_id)
    if transaction_type:
        q = q.filter(models.Transaction.transaction_type == transaction_type.upper())
    return q.order_by(models.Transaction.transaction_date.desc()).all()

@router.post("/", response_model=schemas.TransactionOut, status_code=201)
def create_transaction(
    portfolio_id: int,
    data: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    portfolio = _get_portfolio(portfolio_id, current_user, db)
    stock = db.query(models.Stock).filter(models.Stock.id == data.stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    total = stock.current_price * data.quantity
    txn_type = data.transaction_type.upper()

    if txn_type == "BUY":
        if portfolio.cash_balance < total:
            raise HTTPException(status_code=400, detail="Insufficient cash balance")
        portfolio.cash_balance -= total
    elif txn_type == "SELL":
        # Check holdings
        held = _calculate_holdings(portfolio_id, data.stock_id, db)
        if held < data.quantity:
            raise HTTPException(status_code=400, detail=f"You only hold {held} shares")
        portfolio.cash_balance += total
    else:
        raise HTTPException(status_code=400, detail="transaction_type must be BUY or SELL")

    txn = models.Transaction(
        portfolio_id=portfolio_id,
        stock_id=data.stock_id,
        transaction_type=txn_type,
        quantity=data.quantity,
        price_per_share=stock.current_price,
        total_amount=total,
        notes=data.notes,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn

@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(
    portfolio_id: int,
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _get_portfolio(portfolio_id, current_user, db)
    txn = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.portfolio_id == portfolio_id,
    ).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    # Reverse cash effect
    portfolio = _get_portfolio(portfolio_id, current_user, db)
    if txn.transaction_type == "BUY":
        portfolio.cash_balance += txn.total_amount
    else:
        portfolio.cash_balance -= txn.total_amount
    db.delete(txn)
    db.commit()

def _calculate_holdings(portfolio_id: int, stock_id: int, db: Session) -> int:
    txns = db.query(models.Transaction).filter(
        models.Transaction.portfolio_id == portfolio_id,
        models.Transaction.stock_id == stock_id,
    ).all()
    total = sum(t.quantity if t.transaction_type == "BUY" else -t.quantity for t in txns)
    return total
