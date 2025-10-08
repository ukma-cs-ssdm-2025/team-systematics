from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .errors.app_errors import install_exception_handlers
from .repositories.exams_repository import ExamsRepository
from .repositories.attempts_repository import AttemptsRepository
from .services.exams_service import ExamsService
from .services.attempts_service import AttemptsService as AttemptsSvc
from .controllers.exams_controller import ExamsController
from .controllers.attempts_controller import AttemptsController

def create_app() -> FastAPI:
    app = FastAPI(
        title="Online Exams API",
        version="1.0.0",
        description="Code-first FastAPI spec for an online examination platform.",
        contact={"name": "Team", "email": "team@example.com"},
        license_info={"name": "MIT"},
        servers=[{"url": "http://localhost:3000", "description": "Local dev"}],
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    install_exception_handlers(app)

    exams_repo = ExamsRepository()
    attempts_repo = AttemptsRepository()
    exams_service = ExamsService(exams_repo, attempts_repo)
    attempts_service = AttemptsSvc(attempts_repo)

    exams_controller = ExamsController(exams_service)
    attempts_controller = AttemptsController(attempts_service)

    app.include_router(exams_controller.router, prefix="/api")
    app.include_router(attempts_controller.router, prefix="/api")

    @app.get("/", include_in_schema=False)
    def root():
        return {"status": "ok", "docs": "/docs"}

    return app

app = create_app()