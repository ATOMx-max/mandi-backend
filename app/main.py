from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# 🗄 CREATE DATABASE TABLES HERE
Base.metadata.create_all(bind=engine)

# Root test route
@app.get("/")
def root():
    return {"message": "🚀 Mandi Backend is running!"}
