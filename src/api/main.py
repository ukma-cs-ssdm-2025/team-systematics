import os
import asyncio  # <-- Додано для фонових завдань
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.database import engine  # <-- Імпорт 'engine' перенесено нагору
from src.api.errors.app_errors import install_exception_handlers

# Сервіси
from src.api.services.exams_service import ExamsService
from src.api.services.attempts_service import AttemptsService as AttemptsSvc
from src.api.services.auth_service import AuthService
from src.api.services.exam_review_service import ExamReviewService
from src.api.services.courses_service import CoursesService
from src.api.services.transcript_service import TranscriptService

# Контролери
from src.api.controllers.exams_controller import ExamsController
from src.api.controllers.attempts_controller import AttemptsController
from src.api.controllers.auth_controller import AuthController
from src.api.controllers.courses_controller import CoursesController
from src.api.controllers.transcript_controller import TranscriptController

# Моделі
# Ми імпортуємо 'users' для виклику Base.metadata.create_all()
# SQLAlchemy автоматично знайде всі інші моделі (roles, exams, etc.),
# якщо вони також успадковують той самий Base.
from src.models import (
    users,
    roles,
    user_roles,
    exams,
    courses,
    majors,
    user_majors,
    exam_email_notifications,
)

# Фоновий планувальник
from src.api.background.exam_email_scheduler import run_exam_email_scheduler

# === ВИПРАВЛЕННЯ 1: Створюємо 'set' для зберігання активних фонових завдань ===
background_tasks = set()


def create_app() -> FastAPI:
    # === ВИПРАВЛЕННЯ 2: Створюємо всі таблиці ОДНИМ ВИКЛИКОМ ===
    # Це припускає, що всі ваші моделі (users, roles, exams...)
    # успадковують той самий 'Base' з вашої SQLAlchemy-конфігурації.
    users.Base.metadata.create_all(bind=engine)

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
        "http://localhost:3000",
        "http://localhost:8000",
        "https://systematics-client.onrender.com",
        "https://ukma-cs-ssdm-2025.github.io",
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
    exam_review_service = ExamReviewService()
    auth_service = AuthService()
    transcript_service = TranscriptService()

    # Ініціалізуємо контролери
    exams_controller = ExamsController(exams_service)
    attempts_controller = AttemptsController(attempts_service, exam_review_service)
    auth_controller = AuthController(auth_service)
    courses_controller = CoursesController(CoursesService())
    transcript_controller = TranscriptController(transcript_service)

    # Підключаємо роутери
    app.include_router(auth_controller.router, prefix="/api")
    app.include_router(exams_controller.router, prefix="/api")
    app.include_router(attempts_controller.router, prefix="/api")
    app.include_router(courses_controller.router, prefix="/api")
    app.include_router(transcript_controller.router, prefix="/api")

    # Роздача статичних файлів (фронтенд)
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

    # === ВИПРАВЛЕННЯ 1 (застосування): Зберігаємо завдання у 'set' ===
    @app.on_event("startup")
    async def _start_scheduler():
        task = asyncio.create_task(run_exam_email_scheduler())
        # Додаємо завдання у 'set', щоб зберегти на нього "сильне" посилання
        background_tasks.add(task)
        # Додаємо "зворотний виклик", який видалить завдання з 'set'
        # після його завершення (щоб уникнути витоку пам'яті)
        task.add_done_callback(background_tasks.discard)

    return app


app = create_app()