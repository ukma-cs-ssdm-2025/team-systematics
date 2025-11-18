from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import Request
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.api.errors.app_errors import install_exception_handlers
from src.api.services.exam_status_scheduler import update_exam_statuses
from src.api.services.exams_service import ExamsService
from src.api.services.attempts_service import AttemptsService as AttemptsSvc
from src.api.services.auth_service import AuthService
from src.api.services.exam_review_service import ExamReviewService
from src.api.services.courses_service import CoursesService
from src.api.services.users_service import UsersService
from src.api.controllers.exams_controller import ExamsController
from src.api.controllers.attempts_controller import AttemptsController
from src.api.controllers.auth_controller import AuthController
from src.api.controllers.courses_controller import CoursesController
from src.api.controllers.users_controller import UsersController
from src.models import users, roles, user_roles, exams, courses, majors, user_majors
from src.models import attempts
from src.api.database import SessionLocal, engine
from src.api.controllers.transcript_controller import TranscriptController
from src.api.services.transcript_service import TranscriptService
from src.core.cloudinary import configure_cloudinary
from src.models import exam_participants, course_exams, course_supervisors
from src.api.services.exam_participants_service import ExamParticipantsService
from src.api.controllers.exam_participants_controller import ExamParticipantsController
from src.models import exam_email_notifications 
import asyncio
from src.api.background.exam_email_scheduler import run_exam_email_scheduler


# Глобальна змінна для scheduler
scheduler = None
# Глобальна змінна для асинхронної задачі email-планувальника
email_scheduler_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager для FastAPI.
    Запускає обидва планувальники при старті додатку та зупиняє їх при завершенні.
    """
    global scheduler, email_scheduler_task
    
    # 1. Запуск BackgroundScheduler (для статусів іспитів)
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        update_exam_statuses,
        trigger=IntervalTrigger(minutes=1),
        id='update_exam_statuses',
        name='Update exam statuses from published to open',
        replace_existing=True
    )
    scheduler.start()
    print("BackgroundScheduler started: exam status updates will run every minute")
    update_exam_statuses()
    print("Initial exam status check completed")
    
    # 2. Запуск асинхронного email-планувальника (для сповіщень)
    email_scheduler_task = asyncio.create_task(run_exam_email_scheduler())
    print("Async Email Scheduler task started.")
    
    yield
    
    # Зупиняємо scheduler та скасовуємо асинхронну задачу при завершенні
    if scheduler:
        scheduler.shutdown()
        print("BackgroundScheduler stopped")
    
    if email_scheduler_task:
        email_scheduler_task.cancel()
        print("Async Email Scheduler task cancelled.")


def create_app() -> FastAPI:
    # Створюємо всі таблиці з усіх моделей при старті
    users.Base.metadata.create_all(bind=engine)
    roles.Base.metadata.create_all(bind=engine)
    user_roles.Base.metadata.create_all(bind=engine)
    exams.Base.metadata.create_all(bind=engine)
    courses.Base.metadata.create_all(bind=engine)
    majors.Base.metadata.create_all(bind=engine)
    user_majors.Base.metadata.create_all(bind=engine)
    attempts.Base.metadata.create_all(bind=engine)
    course_exams.Base.metadata.create_all(bind=engine)
    course_supervisors.Base.metadata.create_all(bind=engine)
    exam_participants.Base.metadata.create_all(bind=engine)
    exam_email_notifications.Base.metadata.create_all(bind=engine)

    # Використовуємо lifespan для коректного управління фоновими задачами
    app = FastAPI(
        title="Online Exams API",
        version="1.0.0",
        description="Code-first FastAPI spec for an online examination platform.",
        contact={"name": "Team", "email": "team@example.com"},
        license_info={"name": "MIT"},
        docs_url="/api-docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan, # Підключаємо контекст-менеджер lifespan
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
    users_service = UsersService()
    transcript_service = TranscriptService()
    exam_participants_service = ExamParticipantsService()

    # Ініціалізуємо контролери
    exams_controller = ExamsController(exams_service)
    attempts_controller = AttemptsController(attempts_service, exam_review_service)
    auth_controller = AuthController(auth_service)
    courses_controller = CoursesController(CoursesService())
    transcript_controller = TranscriptController(transcript_service)
    users_controller = UsersController(users_service)
    exam_participants_controller = ExamParticipantsController(exam_participants_service)

    #Ініціалізуємо конфігурацію cloudinary
    # configure_cloudinary() # Закоментовано, якщо потрібна конфігурація з config.py

    # Підключаємо роутери
    app.include_router(auth_controller.router, prefix="/api")
    app.include_router(exams_controller.router, prefix="/api")
    app.include_router(attempts_controller.router, prefix="/api")
    app.include_router(courses_controller.router, prefix="/api")
    app.include_router(transcript_controller.router, prefix="/api")
    app.include_router(users_controller.router, prefix="/api")
    app.include_router(exam_participants_controller.router, prefix="/api")
    
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
    
    # === ВИДАЛЯЄМО ЗАТАРІЛИЙ @app.on_event("startup") ===
    # Тепер запуск run_exam_email_scheduler відбувається у lifespan
    # ==================================================
 
    return app

app = create_app()