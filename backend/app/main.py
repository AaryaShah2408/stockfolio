from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.routers import auth, stocks, portfolios, transactions, watchlist, dashboard

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Stockfolio API",
    description="Stock Portfolio Tracker ",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(stocks.router)
app.include_router(portfolios.router)
app.include_router(transactions.router)
app.include_router(watchlist.router)
app.include_router(dashboard.router)

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Stockfolio API is running"}
