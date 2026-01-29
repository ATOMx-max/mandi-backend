from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import purchases
from app.routes import vendors
from app.routes import inventory
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.gov_data_import import import_gov_prices
from app.routes import trend
from app.ml.train_price_model import train_model





# Import routers
from app.routes import auth, products, prices, negotiations, deals

#DATABASE
from app.database.models import Base
from app.database.db import engine

# Create FastAPI app
app = FastAPI(
    title="Mandi AI Vendor Platform",
    description="Backend for AI-powered price discovery and negotiation",
    version="1.0.0"
)
scheduler = BackgroundScheduler()
# Run every day at 2:00 AM
#scheduler.add_job(import_gov_prices, "cron", hour=2, minute=0)
# 🤖 AI Training Job  ← ADD HERE
def nightly_training():
    print("🤖 Starting nightly AI training...")
    train_model("potato", "azadpur")
    train_model("onion", "lasalgaon")
    print("✅ AI training completed.")
scheduler.add_job(import_gov_prices, "cron", minute=1)
scheduler.start()


# Allow frontend (Android/Web) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Later replace with your app domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route files
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(prices.router, prefix="/prices", tags=["Prices"])
app.include_router(negotiations.router, prefix="/negotiations", tags=["Negotiations"])
app.include_router(deals.router, prefix="/deals", tags=["Deals"])
app.include_router(purchases.router, prefix="/purchases", tags=["Purchases"])
app.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])
app.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
app.include_router(trend.router, prefix="/trends", tags=["Price Trends"])



# 🗄 CREATE DATABASE TABLES HERE
Base.metadata.create_all(bind=engine)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Mandi backend running"}
# Root test route
@app.get("/")
def root():
    return {"message": "🚀 Mandi Backend is running!"}


