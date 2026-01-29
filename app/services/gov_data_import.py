import requests
from app.database.db import SessionLocal
from app.database.models import MarketPrice
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


API_KEY = os.getenv("DATA_GOV_API_KEY")
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"


def import_gov_prices():
    limit = 1000
    offset = 0
    total_imported = 0

    db = SessionLocal()

    try:
        seen = set()
        while True:
            params = {
                "api-key": API_KEY,
                "format": "json",
                "limit": limit,
                "offset": offset
            }

            response = requests.get(BASE_URL, params=params)
            data = response.json()
            records = data.get("records", [])

            if not records:
                break

            for rec in records:
                try:
                    price = float(rec.get("modal_price"))
                except:
                    continue
                # 🚫 Skip unrealistic prices (₹ per quintal)
                if price < 50 or price > 100000:
                    continue
                product = rec.get("commodity", "").strip().lower()
                market = rec.get("market", "").strip().lower()
                date_str = rec.get("arrival_date")
                    # 🚫 Skip bad records
                if not product or not market or price <= 0:
                    continue


                try:
                    arrival_date = datetime.strptime(date_str, "%d/%m/%Y")
                except:
                    arrival_date = datetime.utcnow()

                # 🔍 Avoid duplicates (same product, market, created_at date)
                key = (product, market, arrival_date)
                # Skip if we already saw this in current batch
                if key in seen:
                    continue

                exists = db.query(MarketPrice.id).filter_by(
                    product_name=product,
                    location=market,
                    created_at=arrival_date
                ).first()

                if exists:
                    continue
                seen.add(key)


                mp = MarketPrice(
                    product_name=product,
                    price_per_unit=price,
                    location=market,
                    created_at=arrival_date  # ✅ store mandi date here
                )
                db.add(mp)
                total_imported += 1

            db.commit()
            offset += limit
            logger.info(f"Imported {total_imported} records so far...")

        
        logger.info("✅ Government data import completed!")


    finally:
        db.close()


if __name__ == "__main__":
    import_gov_prices()
