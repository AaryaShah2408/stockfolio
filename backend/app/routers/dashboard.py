from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.core.database import get_db
from app.core.auth import get_current_user
from app import models, schemas

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/portfolio-summary/{portfolio_id}", response_model=schemas.PortfolioSummary)
def portfolio_summary(portfolio_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    portfolio = db.query(models.Portfolio).filter(
        models.Portfolio.id == portfolio_id,
        models.Portfolio.user_id == current_user.id
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    transactions = db.query(models.Transaction).filter(
        models.Transaction.portfolio_id == portfolio_id
    ).all()

    # Aggregate holdings
    holdings_map = {}
    for t in transactions:
        sid = t.stock_id
        if sid not in holdings_map:
            holdings_map[sid] = {"buy_qty": 0, "sell_qty": 0, "buy_total": 0.0}
        if t.transaction_type == "BUY":
            holdings_map[sid]["buy_qty"] += t.quantity
            holdings_map[sid]["buy_total"] += t.total_amount
        else:
            holdings_map[sid]["sell_qty"] += t.quantity

    holdings = []
    total_invested = 0.0
    current_value = 0.0

    for stock_id, h in holdings_map.items():
        net_qty = h["buy_qty"] - h["sell_qty"]
        if net_qty <= 0:
            continue
        stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
        avg_price = h["buy_total"] / h["buy_qty"] if h["buy_qty"] else 0
        invested = avg_price * net_qty
        curr_val = stock.current_price * net_qty
        pnl = curr_val - invested
        pnl_pct = (pnl / invested * 100) if invested else 0

        total_invested += invested
        current_value += curr_val

        holdings.append(schemas.HoldingOut(
            ticker=stock.ticker,
            company_name=stock.company_name,
            sector=stock.sector,
            quantity=net_qty,
            avg_buy_price=round(avg_price, 2),
            current_price=stock.current_price,
            total_invested=round(invested, 2),
            current_value=round(curr_val, 2),
            pnl=round(pnl, 2),
            pnl_pct=round(pnl_pct, 2),
        ))

    total_pnl = current_value - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0

    return schemas.PortfolioSummary(
        portfolio_id=portfolio.id,
        portfolio_name=portfolio.name,
        cash_balance=round(portfolio.cash_balance, 2),
        total_invested=round(total_invested, 2),
        current_value=round(current_value, 2),
        total_pnl=round(total_pnl, 2),
        total_pnl_pct=round(total_pnl_pct, 2),
        holdings=holdings,
    )

@router.get("/sector-allocation/{portfolio_id}", response_model=List[schemas.SectorAllocation])
def sector_allocation(portfolio_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    portfolio = db.query(models.Portfolio).filter(
        models.Portfolio.id == portfolio_id,
        models.Portfolio.user_id == current_user.id
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    transactions = db.query(models.Transaction).filter(models.Transaction.portfolio_id == portfolio_id).all()
    sector_values = {}
    stock_cache = {}

    holdings_map = {}
    for t in transactions:
        sid = t.stock_id
        if sid not in holdings_map:
            holdings_map[sid] = {"buy_qty": 0, "sell_qty": 0}
        if t.transaction_type == "BUY":
            holdings_map[sid]["buy_qty"] += t.quantity
        else:
            holdings_map[sid]["sell_qty"] += t.quantity

    total_val = 0.0
    for stock_id, h in holdings_map.items():
        net_qty = h["buy_qty"] - h["sell_qty"]
        if net_qty <= 0:
            continue
        if stock_id not in stock_cache:
            stock_cache[stock_id] = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
        stock = stock_cache[stock_id]
        val = stock.current_price * net_qty
        sector_values[stock.sector] = sector_values.get(stock.sector, 0) + val
        total_val += val

    result = []
    for sector, val in sector_values.items():
        result.append(schemas.SectorAllocation(
            sector=sector,
            value=round(val, 2),
            percentage=round(val / total_val * 100, 2) if total_val else 0,
        ))
    return sorted(result, key=lambda x: x.value, reverse=True)

@router.get("/top-movers", response_model=List[schemas.StockOut])
def top_movers(limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Returns stocks whose current price differs most from their 30-day average."""
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(days=30)
    subq = (
        db.query(
            models.PriceHistory.stock_id,
            func.avg(models.PriceHistory.close_price).label("avg_price")
        )
        .filter(models.PriceHistory.date >= since)
        .group_by(models.PriceHistory.stock_id)
        .subquery()
    )
    stocks = db.query(models.Stock).join(subq, models.Stock.id == subq.c.stock_id).all()
    stocks_with_change = []
    for s in stocks:
        avg = db.query(func.avg(models.PriceHistory.close_price)).filter(
            models.PriceHistory.stock_id == s.id,
            models.PriceHistory.date >= since
        ).scalar() or s.current_price
        change_pct = abs((s.current_price - avg) / avg * 100) if avg else 0
        stocks_with_change.append((s, change_pct))
    stocks_with_change.sort(key=lambda x: x[1], reverse=True)
    return [s for s, _ in stocks_with_change[:limit]]
