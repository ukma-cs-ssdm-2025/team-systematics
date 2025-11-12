from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.core.config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found. Check your .env file!")

# Додаємо таймаути для з'єднань з БД
# connect_args для SQLite, pool_pre_ping для перевірки з'єднань перед використанням
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Перевіряє з'єднання перед використанням
    connect_args={
        "connect_timeout": 10,  # Таймаут підключення (секунди)
        "options": "-c statement_timeout=30000"  # Таймаут виконання запиту (30 секунд для PostgreSQL)
    } if "postgresql" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
