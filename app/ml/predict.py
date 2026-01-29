import joblib
import numpy as np
import os

MODEL_DIR = os.path.dirname(__file__)


def predict_next_price(product_name: str, location: str, current_length: int):
    model_path = os.path.join(MODEL_DIR, f"{product_name}_{location}_model.pkl")

    if not os.path.exists(model_path):
        return None

    model = joblib.load(model_path)
    next_day = np.array([[current_length]])

    return float(model.predict(next_day)[0])
