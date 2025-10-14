from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_auth
from app.core.config import DATABASE_URL
print("DATABASE_URL =", DATABASE_URL)

app = FastAPI(title="Systematics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # або ['http://localhost:5173']
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_auth.router, prefix="/api/auth", tags=["Auth"])
