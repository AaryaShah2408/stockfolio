# Stockfolio — Stock Portfolio Tracker

DBMS Course Project | FastAPI + PostgreSQL + Vanilla JS Dashboard

---

## Project Structure

```
stockfolio/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── models.py            # SQLAlchemy ORM models (6 tables)
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── core/
│   │   │   ├── config.py        # Settings from .env
│   │   │   ├── database.py      # DB engine + session
│   │   │   └── auth.py          # JWT auth + password hashing
│   │   └── routers/
│   │       ├── auth.py          # /auth/register /auth/login /auth/me
│   │       ├── stocks.py        # GET/PATCH stocks, price history
│   │       ├── portfolios.py    # Full CRUD on portfolios
│   │       ├── transactions.py  # BUY/SELL transactions
│   │       ├── watchlist.py     # Add/remove watchlist items
│   │       └── dashboard.py     # Analytics endpoints
│   ├── seed.py                  # Populates DB with ~14,000 rows
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── index.html               # Complete single-file dashboard
```

---

## Database Schema

| Table          | Key Columns                                              | Purpose                         |
|----------------|----------------------------------------------------------|---------------------------------|
| `users`        | id, username, email, hashed_password                    | Auth & user management          |
| `stocks`       | id, ticker, sector, current_price, pe_ratio, 52w_high   | Stock master data               |
| `price_history`| stock_id, date, open, high, low, close, volume          | OHLCV time-series (~14k rows)   |
| `portfolios`   | id, user_id, name, cash_balance                         | User portfolios                 |
| `transactions` | portfolio_id, stock_id, type, quantity, price           | BUY/SELL trade log              |
| `watchlists`   | user_id, stock_id, target_price                         | Per-user watchlist              |

---

## API Endpoints

| Method | Route | Auth | Purpose |
|--------|-------|------|---------|
| POST | /auth/register | No | Create account |
| POST | /auth/login | No | Get JWT token |
| GET | /auth/me | Yes | Current user info |
| GET | /stocks/ | Yes | List/search/filter stocks |
| GET | /stocks/sectors | Yes | List sectors |
| GET | /stocks/{id} | Yes | Get single stock |
| PATCH | /stocks/{id} | Yes | Update stock price/PE |
| GET | /stocks/{id}/history | Yes | OHLCV price history |
| GET | /portfolios/ | Yes | List my portfolios |
| POST | /portfolios/ | Yes | Create portfolio |
| GET | /portfolios/{id} | Yes | Get portfolio |
| PATCH | /portfolios/{id} | Yes | Update portfolio |
| DELETE | /portfolios/{id} | Yes | Delete portfolio |
| GET | /portfolios/{id}/transactions/ | Yes | List transactions |
| POST | /portfolios/{id}/transactions/ | Yes | Create BUY/SELL |
| DELETE | /portfolios/{id}/transactions/{tid} | Yes | Delete transaction |
| GET | /watchlist/ | Yes | My watchlist |
| POST | /watchlist/ | Yes | Add to watchlist |
| DELETE | /watchlist/{id} | Yes | Remove from watchlist |
| GET | /dashboard/portfolio-summary/{id} | Yes | Holdings + P&L summary |
| GET | /dashboard/sector-allocation/{id} | Yes | Sector breakdown |
| GET | /dashboard/top-movers | Yes | Top volatile stocks |

---

## Local Setup (Step by Step)

### Step 1 — Create PostgreSQL Database

1. Open **DBeaver**
2. Connect to your local PostgreSQL server
3. Right-click Databases → Create New Database
4. Name it: `stockfolio`
5. Click OK

### Step 2 — Configure Environment

```bash
cd stockfolio/backend
cp .env.example .env
```

Edit `.env`:
```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/stockfolio
SECRET_KEY=any-long-random-string-here
```

### Step 3 — Install Python Dependencies

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Step 4 — Seed the Database

```bash
python seed.py
```

Expected output:
```
Seeding stocks...
Seeding price history (~14,000 rows)...
Seeding demo users...
Seeding demo portfolio...
Seeding watchlist...

✅ Seed complete!
   Demo login → username: demo  |  password: demo1234
```

You can verify in DBeaver — open the `stockfolio` database, expand Tables, and check the row counts.

### Step 5 — Run the API

```bash
uvicorn app.main:app --reload
```

API is live at: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

### Step 6 — Open the Frontend

Simply open `frontend/index.html` in your browser.

Login with:
- Username: `demo`
- Password: `demo1234`

---

## Dashboard Features

| Feature | Description |
|---------|-------------|
| Portfolio Summary | 4 KPI cards: Invested, Current Value, P&L, Cash |
| Price History Chart | Line chart with 1M/3M/6M/1Y selector per stock |
| Sector Allocation | Doughnut chart of holdings by sector |
| Top Movers | Horizontal bar chart of most volatile stocks |
| Holdings Table | Full breakdown with avg buy price, LTP, P&L per holding |
| Stock Browser | Search + sector filter across all 40 stocks |
| Buy / Sell | Real-time trade execution with balance validation |
| Transactions | Full trade history with delete/reverse |
| Watchlist | Add stocks with target price alerts |
| Auto Refresh | Dashboard refreshes every 20 seconds |

---

## Sample SQL Queries (for Report)

```sql
-- 1. Portfolio P&L per holding
SELECT s.ticker, s.company_name,
  SUM(CASE WHEN t.transaction_type='BUY' THEN t.quantity ELSE -t.quantity END) AS net_qty,
  AVG(CASE WHEN t.transaction_type='BUY' THEN t.price_per_share END) AS avg_buy_price,
  s.current_price,
  (s.current_price - AVG(CASE WHEN t.transaction_type='BUY' THEN t.price_per_share END))
    * SUM(CASE WHEN t.transaction_type='BUY' THEN t.quantity ELSE -t.quantity END) AS unrealized_pnl
FROM transactions t
JOIN stocks s ON t.stock_id = s.id
WHERE t.portfolio_id = 1
GROUP BY s.id, s.ticker, s.company_name, s.current_price;

-- 2. Sector allocation by market value
SELECT s.sector, SUM(s.current_price * net_holdings.qty) AS sector_value
FROM (
  SELECT stock_id,
    SUM(CASE WHEN transaction_type='BUY' THEN quantity ELSE -quantity END) AS qty
  FROM transactions WHERE portfolio_id = 1
  GROUP BY stock_id
) net_holdings
JOIN stocks s ON net_holdings.stock_id = s.id
WHERE net_holdings.qty > 0
GROUP BY s.sector ORDER BY sector_value DESC;

-- 3. 30-day price volatility (std deviation)
SELECT s.ticker, STDDEV(ph.close_price) AS volatility, AVG(ph.close_price) AS avg_price
FROM price_history ph
JOIN stocks s ON ph.stock_id = s.id
WHERE ph.date >= NOW() - INTERVAL '30 days'
GROUP BY s.ticker ORDER BY volatility DESC LIMIT 10;

-- 4. Monthly transaction volume
SELECT DATE_TRUNC('month', transaction_date) AS month,
  COUNT(*) AS total_trades,
  SUM(total_amount) AS total_value
FROM transactions
GROUP BY month ORDER BY month;

-- 5. User portfolio summary
SELECT u.username, p.name, p.cash_balance,
  COUNT(DISTINCT t.stock_id) AS stocks_held,
  SUM(CASE WHEN t.transaction_type='BUY' THEN t.total_amount ELSE 0 END) AS total_invested
FROM users u
JOIN portfolios p ON u.id = p.user_id
LEFT JOIN transactions t ON p.id = t.portfolio_id
GROUP BY u.username, p.name, p.cash_balance;
```

---

## Demo Credentials

| Username | Password | Role |
|----------|----------|------|
| demo | demo1234 | Pre-seeded with portfolio & transactions |
| alice | alice1234 | Empty account |

---

## Tech Stack

- **Database**: PostgreSQL (OLTP — ACID for financial transactions)
- **ORM**: SQLAlchemy 2.0
- **API**: FastAPI + Pydantic v2
- **Auth**: JWT (python-jose) + bcrypt (passlib)
- **Frontend**: Vanilla JS + Chart.js 4
- **DB Tool**: DBeaver (schema exploration + ER diagram generation)
