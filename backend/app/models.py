from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    portfolios = relationship("Portfolio", back_populates="user")
    watchlists = relationship("Watchlist", back_populates="user")

class Stock(Base):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), unique=True, nullable=False, index=True)
    company_name = Column(String(150), nullable=False)
    sector = Column(String(80), nullable=False)
    exchange = Column(String(20), default="NSE")
    current_price = Column(Float, nullable=False)
    market_cap = Column(Float)
    pe_ratio = Column(Float)
    week_52_high = Column(Float)
    week_52_low = Column(Float)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    price_history = relationship("PriceHistory", back_populates="stock")
    transactions = relationship("Transaction", back_populates="stock")
    watchlists = relationship("Watchlist", back_populates="stock")

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    cash_balance = Column(Float, default=100000.0)

    user = relationship("User", back_populates="portfolios")
    transactions = relationship("Transaction", back_populates="portfolio")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    transaction_type = Column(String(4), nullable=False)  # BUY or SELL
    quantity = Column(Integer, nullable=False)
    price_per_share = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    transaction_date = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)

    portfolio = relationship("Portfolio", back_populates="transactions")
    stock = relationship("Stock", back_populates="transactions")

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer)

    stock = relationship("Stock", back_populates="price_history")

class Watchlist(Base):
    __tablename__ = "watchlists"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    target_price = Column(Float)
    notes = Column(Text)

    user = relationship("User", back_populates="watchlists")
    stock = relationship("Stock", back_populates="watchlists")
