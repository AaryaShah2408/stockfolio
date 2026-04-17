from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ── Auth ──────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    class Config: from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# ── Stock ─────────────────────────────────────────────
class StockOut(BaseModel):
    id: int
    ticker: str
    company_name: str
    sector: str
    exchange: str
    current_price: float
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    week_52_high: Optional[float]
    week_52_low: Optional[float]
    class Config: from_attributes = True

class StockUpdate(BaseModel):
    current_price: Optional[float] = None
    pe_ratio: Optional[float] = None
    market_cap: Optional[float] = None

# ── Portfolio ─────────────────────────────────────────
class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    cash_balance: Optional[float] = 100000.0

class PortfolioOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    cash_balance: float
    created_at: datetime
    class Config: from_attributes = True

class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

# ── Transaction ───────────────────────────────────────
class TransactionCreate(BaseModel):
    stock_id: int
    transaction_type: str   # BUY or SELL
    quantity: int
    notes: Optional[str] = None

class TransactionOut(BaseModel):
    id: int
    portfolio_id: int
    stock_id: int
    transaction_type: str
    quantity: int
    price_per_share: float
    total_amount: float
    transaction_date: datetime
    notes: Optional[str]
    class Config: from_attributes = True

# ── Watchlist ─────────────────────────────────────────
class WatchlistCreate(BaseModel):
    stock_id: int
    target_price: Optional[float] = None
    notes: Optional[str] = None

class WatchlistOut(BaseModel):
    id: int
    stock_id: int
    added_at: datetime
    target_price: Optional[float]
    notes: Optional[str]
    stock: StockOut
    class Config: from_attributes = True

# ── Dashboard ─────────────────────────────────────────
class HoldingOut(BaseModel):
    ticker: str
    company_name: str
    sector: str
    quantity: int
    avg_buy_price: float
    current_price: float
    total_invested: float
    current_value: float
    pnl: float
    pnl_pct: float

class PortfolioSummary(BaseModel):
    portfolio_id: int
    portfolio_name: str
    cash_balance: float
    total_invested: float
    current_value: float
    total_pnl: float
    total_pnl_pct: float
    holdings: List[HoldingOut]

class SectorAllocation(BaseModel):
    sector: str
    value: float
    percentage: float

class PriceHistoryOut(BaseModel):
    date: datetime
    close_price: float
    volume: Optional[int]
    class Config: from_attributes = True
