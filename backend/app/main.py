from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_auth, routes_exam # <-- Імпортуємо роутер іспитів
from app.db.session import engine
from app.models import user, role, user_role, exam # <-- Імпортуємо моделі іспитів

# Створюємо всі таблиці в базі даних при старті додатку
user.Base.metadata.create_all(bind=engine)
role.Base.metadata.create_all(bind=engine)
user_role.Base.metadata.create_all(bind=engine)
exam.Base.metadata.create_all(bind=engine) # <-- Створюємо таблиці для іспитів

app = FastAPI(title="Systematics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Підключаємо роутери
app.include_router(routes_auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(routes_exam.router, prefix="/api", tags=["Exams"]) # <-- Підключаємо роутер іспитів