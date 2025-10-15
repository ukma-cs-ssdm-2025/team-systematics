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

from .errors.app_errors import install_exception_handlers   
import os
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.responses import FileResponse

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


    # This gets the directory where this main.py file is located
    current_file_path = os.path.dirname(os.path.abspath(__file__))
    # This constructs the correct path to the 'dist' folder
    build_dir = os.path.join(current_file_path, "../../client/dist")

    # Path to the assets directory
    assets_dir = os.path.join(build_dir, "assets")
    print(assets_dir)

    # Mount the static assets directory
    # This will serve files like /assets/index-*.js and /assets/index-*.css
    app.mount(
        "/assets",
        StaticFiles(directory=assets_dir),
        name="assets",
    )

    # Catch-all route to serve the 'index.html' for any other path
    # This is essential for SPAs with client-side routing
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_vue_app(request: Request):
        index_path = os.path.join(build_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"error": "index.html not found"}

    # Serve index.html on root path
    @app.get("/", include_in_schema=False)
    async def root():
        index_path = os.path.join(build_dir, "index.html")
        return FileResponse(index_path)


    return app

app = create_app()
