from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import Request
from src.api.errors.app_errors import install_exception_handlers
from src.api.services.exams_service import ExamsService
from src.api.services.attempts_service import AttemptsService as AttemptsSvc
from src.api.services.auth_service import AuthService
from src.api.controllers.exams_controller import ExamsController
from src.api.controllers.attempts_controller import AttemptsController
from src.api.controllers.auth_controller import AuthController
from src.api.database import engine
from src.models import user, role, user_role, exam

def create_app() -> FastAPI:
    # Створюємо всі таблиці з усіх моделей при старті
    user.Base.metadata.create_all(bind=engine)
    role.Base.metadata.create_all(bind=engine)
    user_role.Base.metadata.create_all(bind=engine)
    exam.Base.metadata.create_all(bind=engine)

    app = FastAPI(
        title="Online Exams API",
        version="1.0.0",
        description="Code-first FastAPI spec for an online examination platform.",
        contact={"name": "Team", "email": "team@example.com"},
        license_info={"name": "MIT"},
        docs_url="/api-docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    origins = [
        "http://localhost:5173",
        "https://ukma-cs-ssdm-2025.github.io"
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    install_exception_handlers(app)

    # Ініціалізуємо сервіси
    exams_service = ExamsService()
    attempts_service = AttemptsSvc()
    auth_service = AuthService()

    # Ініціалізуємо контролери
    exams_controller = ExamsController(exams_service)
    attempts_controller = AttemptsController(attempts_service)
    auth_controller = AuthController(auth_service)

    # Підключаємо роутери
    app.include_router(auth_controller.router, prefix="/api")
    app.include_router(exams_controller.router, prefix="/api")
    app.include_router(attempts_controller.router, prefix="/api")
    
    # ... (код для роздачі статичних файлів фронтенду залишається без змін) ...
    current_file_path = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(current_file_path, "../../client/dist")

    if os.path.exists(build_dir):
        assets_dir = os.path.join(build_dir, "assets")
        if os.path.exists(assets_dir):
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_vue_app(request: Request):
            index_path = os.path.join(build_dir, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            return {"error": "index.html not found"}

    return app

app = create_app()