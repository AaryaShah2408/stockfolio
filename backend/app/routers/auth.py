from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import hash_password, verify_password, create_access_token
from app import models, schemas

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(__import__("app.core.auth", fromlist=["get_current_user"]).get_current_user)):
    return current_user

@router.post("/seed-db", include_in_schema=False)
def seed_database(db: Session = Depends(get_db)):
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "seed.py"],
        capture_output=True, text=True
    )
    return {"output": result.stdout, "errors": result.stderr}

@router.post("/seed-db", include_in_schema=False)
def seed_database(db: Session = Depends(get_db)):
    from app import models
    from app.core.auth import hash_password
    import random
    from datetime import datetime, timedelta

    STOCKS = [
        ("TCS","Tata Consultancy Services","IT",3850.0),
        ("INFY","Infosys Ltd","IT",1420.0),
        ("WIPRO","Wipro Ltd","IT",480.0),
        ("HDFCBANK","HDFC Bank","Banking",1620.0),
        ("ICICIBANK","ICICI Bank","Banking",1050.0),
        ("SBIN","State Bank of India","Banking",750.0),
        ("SUNPHARMA","Sun Pharmaceutical","Pharma",1680.0),
        ("RELIANCE","Reliance Industries","Energy",2950.0),
        ("HINDUNILVR","Hindustan Unilever","FMCG",2450.0),
        ("ITC","ITC Ltd","FMCG",460.0),
        ("MARUTI","Maruti Suzuki India","Auto",12500.0),
        ("TATAMOTORS","Tata Motors","Auto",940.0),
        ("TATASTEEL","Tata Steel","Metals",165.0),
        ("BHARTIARTL","Bharti Airtel","Telecom",1350.0),
        ("LT","Larsen & Toubro","Infra",3600.0),
    ]

    stock_objs = []
    for ticker, name, sector, price in STOCKS:
        s = db.query(models.Stock).filter(models.Stock.ticker == ticker).first()
        if not s:
            s = models.Stock(
                ticker=ticker, company_name=name, sector=sector,
                exchange="NSE", current_price=price,
                market_cap=price * random.randint(500000000, 5000000000),
                pe_ratio=round(random.uniform(10,50),2),
                week_52_high=round(price*random.uniform(1.05,1.40),2),
                week_52_low=round(price*random.uniform(0.60,0.95),2),
            )
            db.add(s)
        stock_objs.append(s)
    db.commit()
    for s in stock_objs:
        db.refresh(s)

    for stock in stock_objs:
        count = db.query(models.PriceHistory).filter(models.PriceHistory.stock_id == stock.id).count()
        if count > 10:
            continue
        price = stock.current_price * random.uniform(0.70, 0.90)
        base_date = datetime.utcnow() - timedelta(days=365)
        for day in range(365):
            date = base_date + timedelta(days=day)
            if date.weekday() >= 5:
                continue
            change = random.gauss(0, 0.015)
            price = max(price * (1 + change), 1.0)
            db.add(models.PriceHistory(
                stock_id=stock.id, date=date,
                open_price=round(price*random.uniform(0.98,1.02),2),
                high_price=round(price*random.uniform(1.00,1.025),2),
                low_price=round(price*random.uniform(0.975,1.00),2),
                close_price=round(price,2),
                volume=random.randint(100000,5000000),
            ))
        stock.current_price = round(price, 2)
    db.commit()

    for uname, email, pwd in [("demo","demo@stockfolio.com","demo1234"),("alice","alice@example.com","alice1234")]:
        if not db.query(models.User).filter(models.User.username == uname).first():
            db.add(models.User(username=uname, email=email, hashed_password=hash_password(pwd)))
    db.commit()

    demo_user = db.query(models.User).filter(models.User.username == "demo").first()
    if not db.query(models.Portfolio).filter(models.Portfolio.user_id == demo_user.id).first():
        port = models.Portfolio(user_id=demo_user.id, name="My Main Portfolio", cash_balance=500000.0)
        db.add(port)
        db.commit()
        db.refresh(port)
        for stock in random.sample(stock_objs, 5):
            qty = random.randint(5,20)
            price = stock.current_price * random.uniform(0.80,0.95)
            total = price * qty
            port.cash_balance -= total
            db.add(models.Transaction(
                portfolio_id=port.id, stock_id=stock.id,
                transaction_type="BUY", quantity=qty,
                price_per_share=round(price,2), total_amount=round(total,2),
                transaction_date=datetime.utcnow()-timedelta(days=random.randint(10,180)),
            ))
        db.commit()

    return {"status": "✅ Seed complete! Login with demo / demo1234"}