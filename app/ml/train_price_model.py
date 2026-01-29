import numpy as np
from sklearn.linear_model import LinearRegression
import joblib
import os

from app.database.db import SessionLocal
from app.database.models import MarketPrice

MODEL_DIR = os.path.dirname(__file__)


def train_model(product_name: str, location: str):
    db = SessionLocal()

    prices = db.query(MarketPrice.price_per_unit)\
        .filter(
            MarketPrice.product_name.ilike(f"%{product_name.lower()}%"),
            MarketPrice.location.ilike(f"%{location.lower()}%")
        )\
        .order_by(MarketPrice.created_at.asc())\
        .all()

    db.close()

    price_list = [p[0] for p in prices]

    if len(price_list) < 5:
        print(f"Not enough data to train model for {product_name} at {location}")
        return

    X = np.array(range(len(price_list))).reshape(-1, 1)
    y = np.array(price_list)

    model = LinearRegression()
    model.fit(X, y)

    model_path = os.path.join(MODEL_DIR, f"{product_name}_{location}_model.pkl")
    joblib.dump(model, model_path)

    print(f"✅ Model trained for {product_name} at {location}")
