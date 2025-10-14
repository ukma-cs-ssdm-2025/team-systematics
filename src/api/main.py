from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .errors.app_errors import install_exception_handlers

from .repositories.exams_repository import ExamsRepository
from .repositories.attempts_repository import AttemptsRepository
from .repositories.user_repository import UserRepository

from .services.exams_service import ExamsService
from .services.attempts_service import AttemptsService as AttemptsSvc
from .services.auth_service import AuthService

from .controllers.exams_controller import ExamsController
from .controllers.attempts_controller import AttemptsController
from .controllers.auth_controller import AuthController


def create_app() -> FastAPI:
    servers = [
        {"url": "https://systematics.onrender.com", "description": "Production server"},
        {"url": "http://127.0.0.1:8000", "description": "Local development server"},
    ]

    app = FastAPI(
        title="Online Exams API",
        version="1.0.0",
        description="Code-first FastAPI spec for an online examination platform.",
        contact={"name": "Team", "email": "team@example.com"},
        license_info={"name": "MIT"},
        servers=servers,
        docs_url="/api-docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
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

    exams_repo = ExamsRepository()
    attempts_repo = AttemptsRepository()
    user_repo = UserRepository(None)

    exams_service = ExamsService(exams_repo, attempts_repo)
    attempts_service = AttemptsSvc(attempts_repo)
    auth_service = AuthService()

    exams_controller = ExamsController(exams_service)
    attempts_controller = AttemptsController(attempts_service)
    auth_controller = AuthController(auth_service)

    app.include_router(exams_controller.router, prefix="/api")
    app.include_router(attempts_controller.router, prefix="/api")
    app.include_router(auth_controller.router, prefix="/api")

    @app.get("/", include_in_schema=False)
    def root():
        return {"status": "ok", "docs": "/api-docs"}

    return app

app = create_app()
