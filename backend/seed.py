"""
Run once to populate the database with realistic stock market data.
Usage: python seed.py
"""

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import random
from app.core.database import SessionLocal, engine, Base
from app.core.auth import hash_password
from app import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ── Stocks (Indian market flavour) ────────────────────────────────────────────
STOCKS = [
    # IT
    ("TCS",    "Tata Consultancy Services",   "IT",          3850.0),
    ("INFY",   "Infosys Ltd",                 "IT",          1420.0),
    ("WIPRO",  "Wipro Ltd",                   "IT",           480.0),
    ("HCLTECH","HCL Technologies",            "IT",          1300.0),
    ("TECHM",  "Tech Mahindra",               "IT",          1150.0),
    # Banking
    ("HDFCBANK","HDFC Bank",                  "Banking",     1620.0),
    ("ICICIBANK","ICICI Bank",                "Banking",     1050.0),
    ("SBIN",   "State Bank of India",         "Banking",      750.0),
    ("AXISBANK","Axis Bank",                  "Banking",      980.0),
    ("KOTAKBANK","Kotak Mahindra Bank",       "Banking",     1780.0),
    # Pharma
    ("SUNPHARMA","Sun Pharmaceutical",        "Pharma",      1680.0),
    ("DRREDDY", "Dr Reddy's Laboratories",    "Pharma",      5900.0),
    ("CIPLA",  "Cipla Ltd",                   "Pharma",      1400.0),
    ("DIVISLAB","Divi's Laboratories",        "Pharma",      3800.0),
    ("BIOCON", "Biocon Ltd",                  "Pharma",       290.0),
    # Energy
    ("RELIANCE","Reliance Industries",        "Energy",      2950.0),
    ("ONGC",   "Oil & Natural Gas Corp",      "Energy",       280.0),
    ("NTPC",   "NTPC Ltd",                    "Energy",       380.0),
    ("POWERGRID","Power Grid Corporation",    "Energy",       310.0),
    ("BPCL",   "Bharat Petroleum Corp",       "Energy",       620.0),
    # FMCG
    ("HINDUNILVR","Hindustan Unilever",       "FMCG",        2450.0),
    ("ITC",    "ITC Ltd",                     "FMCG",         460.0),
    ("NESTLEIND","Nestle India",              "FMCG",        2300.0),
    ("BRITANNIA","Britannia Industries",      "FMCG",        5100.0),
    ("DABUR",  "Dabur India",                 "FMCG",         540.0),
    # Auto
    ("MARUTI", "Maruti Suzuki India",         "Auto",       12500.0),
    ("TATAMOTORS","Tata Motors",              "Auto",         940.0),
    ("M&M",    "Mahindra & Mahindra",         "Auto",        1900.0),
    ("BAJAJ-AUTO","Bajaj Auto",              "Auto",         8800.0),
    ("HEROMOTOCO","Hero MotoCorp",            "Auto",         4200.0),
    # Metals
    ("TATASTEEL","Tata Steel",               "Metals",       165.0),
    ("HINDALCO","Hindalco Industries",        "Metals",       580.0),
    ("JSWSTEEL","JSW Steel",                 "Metals",       890.0),
    ("COALINDIA","Coal India",               "Metals",       450.0),
    ("VEDL",   "Vedanta Ltd",                 "Metals",       425.0),
    # Telecom
    ("BHARTIARTL","Bharti Airtel",           "Telecom",     1350.0),
    ("IDEA",   "Vodafone Idea",              "Telecom",        14.0),
    # Infra
    ("LT",     "Larsen & Toubro",            "Infra",        3600.0),
    ("ULTRACEMCO","UltraTech Cement",        "Infra",       10500.0),
    ("ADANIPORTS","Adani Ports & SEZ",       "Infra",        1250.0),
]

print("Seeding stocks...")
stock_objs = []
for ticker, name, sector, price in STOCKS:
    existing = db.query(models.Stock).filter(models.Stock.ticker == ticker).first()
    if existing:
        stock_objs.append(existing)
        continue
    s = models.Stock(
        ticker=ticker,
        company_name=name,
        sector=sector,
        exchange="NSE",
        current_price=price,
        market_cap=price * random.randint(500_000_000, 5_000_000_000),
        pe_ratio=round(random.uniform(10, 50), 2),
        week_52_high=round(price * random.uniform(1.05, 1.40), 2),
        week_52_low=round(price * random.uniform(0.60, 0.95), 2),
    )
    db.add(s)
    stock_objs.append(s)

db.commit()
for s in stock_objs:
    db.refresh(s)

# ── Price History (365 days per stock) ────────────────────────────────────────
print("Seeding price history (~14,000 rows)...")
for stock in stock_objs:
    # Check if already seeded
    count = db.query(models.PriceHistory).filter(models.PriceHistory.stock_id == stock.id).count()
    if count > 100:
        continue

    price = stock.current_price * random.uniform(0.70, 0.90)   # start lower
    base_date = datetime.utcnow() - timedelta(days=365)

    for day in range(365):
        date = base_date + timedelta(days=day)
        if date.weekday() >= 5:   # skip weekends
            continue
        change = random.gauss(0, 0.015)          # daily return ~1.5% std
        price = max(price * (1 + change), 1.0)
        open_p = price * random.uniform(0.98, 1.02)
        high_p = price * random.uniform(1.00, 1.025)
        low_p  = price * random.uniform(0.975, 1.00)
        vol    = random.randint(100_000, 5_000_000)
        db.add(models.PriceHistory(
            stock_id=stock.id,
            date=date,
            open_price=round(open_p, 2),
            high_price=round(high_p, 2),
            low_price=round(low_p, 2),
            close_price=round(price, 2),
            volume=vol,
        ))
    # Update current price to match last generated price
    stock.current_price = round(price, 2)

db.commit()

# ── Demo Users ────────────────────────────────────────────────────────────────
print("Seeding demo users...")
demo_users = [
    ("demo", "demo@stockfolio.com", "demo1234"),
    ("alice", "alice@example.com", "alice1234"),
]
user_objs = []
for uname, email, pwd in demo_users:
    u = db.query(models.User).filter(models.User.username == uname).first()
    if not u:
        u = models.User(username=uname, email=email, hashed_password=hash_password(pwd))
        db.add(u)
    user_objs.append(u)
db.commit()
for u in user_objs:
    db.refresh(u)

# ── Demo Portfolio with Transactions ─────────────────────────────────────────
print("Seeding demo portfolio...")
demo_user = user_objs[0]
port = db.query(models.Portfolio).filter(models.Portfolio.user_id == demo_user.id).first()
if not port:
    port = models.Portfolio(user_id=demo_user.id, name="My Main Portfolio", description="Demo portfolio", cash_balance=500000.0)
    db.add(port)
    db.commit()
    db.refresh(port)

    # Buy a mix of stocks over past 6 months
    sample_stocks = random.sample(stock_objs, 12)
    for stock in sample_stocks:
        qty = random.randint(5, 50)
        price = stock.current_price * random.uniform(0.80, 0.95)
        total = price * qty
        port.cash_balance -= total
        txn_date = datetime.utcnow() - timedelta(days=random.randint(10, 180))
        db.add(models.Transaction(
            portfolio_id=port.id,
            stock_id=stock.id,
            transaction_type="BUY",
            quantity=qty,
            price_per_share=round(price, 2),
            total_amount=round(total, 2),
            transaction_date=txn_date,
        ))
    db.commit()

# ── Demo Watchlist ────────────────────────────────────────────────────────────
print("Seeding watchlist...")
watch_stocks = random.sample(stock_objs, 5)
for stock in watch_stocks:
    existing = db.query(models.Watchlist).filter(
        models.Watchlist.user_id == demo_user.id,
        models.Watchlist.stock_id == stock.id
    ).first()
    if not existing:
        db.add(models.Watchlist(
            user_id=demo_user.id,
            stock_id=stock.id,
            target_price=round(stock.current_price * 1.10, 2),
        ))
db.commit()
db.close()

print("\n✅ Seed complete!")
print("   Demo login → username: demo  |  password: demo1234")
