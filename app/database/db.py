from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL

#define hardcore
DATABASE_URL = "mysql+pymysql://mandiuser:Mandi%40123@localhost/mandi"
print("Using DB URL:", DATABASE_URL)
# Create connection to MySQL
engine = create_engine(DATABASE_URL, echo=True)

# Each API request will use its own DB session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all database tables
Base = declarative_base()

# Dependency used in routes later
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
