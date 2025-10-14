from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Завантажуємо змінні з файлу .env (щоб не тримати паролі прямо в коді)
load_dotenv()

# Отримуємо URL бази даних із змінної середовища
DATABASE_URL = os.getenv("DATABASE_URL")

# Створюємо "движок" для роботи з базою через SQLAlchemy
engine = create_engine(DATABASE_URL)

# Налаштовуємо фабрику сесій для взаємодії з базою даних
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовий клас для створення моделей (таблиць)
Base = declarative_base()

# Функція-залежність для FastAPI — створює та закриває сесію з БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()