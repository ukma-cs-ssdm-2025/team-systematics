from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Query, Path, status, Depends
from uuid import UUID
from src.api.schemas.exams import Exam, ExamCreate, ExamUpdate, ExamsPage, CourseExamsPage
from src.api.schemas.journal import ExamJournalResponse
from src.api.schemas.attempts import Attempt
from src.models.users import User
from src.utils.auth import get_current_user_id, get_current_user, get_current_user_with_role 
from src.api.services.exams_service import ExamsService
from src.api.services.journal_service import JournalService
from .versioning import require_api_version
from src.api.database import get_db

class ExamsController:
    def __init__(self, service: ExamsService) -> None:
        self.service = service
        self.journal_service = JournalService()
        self.router = APIRouter(prefix="/exams", tags=["Exams"], dependencies=[Depends(require_api_version)])

        # --- CRUD-Ендпойнти ---

        @self.router.get("", summary="List exams")
        async def list_exams(
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user),
            limit: int = Query(10, ge=1, le=100),
            offset: int = Query(0, ge=0)
            ):
            try:
                return self.service.list(db, user_id=current_user.id, limit=limit, offset=offset)
            except HTTPException as he:
                # Re-raise HTTP exceptions (validation errors, etc.)
                raise he
            except Exception as e:
                # Handle unexpected errors (including database failures)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "code": "INTERNAL_ERROR",
                        "message": str(e)
                    }
                )

        @self.router.post("", response_model=Exam, status_code=status.HTTP_201_CREATED, summary="Create exam")
        async def create_exam(payload: ExamCreate, db: Session = Depends(get_db)):
            try:
                return self.service.create(db, payload)
            except HTTPException as he:
                # Re-raise HTTP exceptions (validation errors, etc.)
                raise he
            except Exception as e:
                # Handle unexpected errors
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "code": "INTERNAL_ERROR",
                        "message": str(e)
                    }
                )

        @self.router.get("/{exam_id}", response_model=Exam, summary="Get exam by id")
        async def get_exam(exam_id: UUID, db: Session = Depends(get_db)):
            return self.service.get(db, exam_id)

        @self.router.patch("/{exam_id}", response_model=Exam, summary="Update exam (partial)")
        async def update_exam(patch: ExamUpdate, exam_id: UUID, db: Session = Depends(get_db)):
            return self.service.update(db, exam_id, patch)

        @self.router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete exam")
        async def delete_exam(exam_id: UUID, db: Session = Depends(get_db)):
            self.service.delete(db, exam_id)
            return None

        # --- Керування спробами іспиту ---

        @self.router.post("/{exam_id}/attempts", response_model=Attempt, status_code=status.HTTP_201_CREATED, summary="Start an attempt for exam")
        async def start_attempt(user_id: UUID = Depends(get_current_user_id), exam_id: UUID = Path(...), db: Session = Depends(get_db)):
            return self.service.start_attempt(db, exam_id, user_id)

        # --- Ендпойнти для питань іспиту ---
        @self.router.post("/{exam_id}/questions", status_code=status.HTTP_201_CREATED, summary="Create question for exam")
        async def create_question(exam_id: UUID, payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
            return self.service.create_question(db, exam_id, payload)

        @self.router.patch("/{exam_id}/questions/{question_id}", summary="Update question")
        async def update_question(exam_id: UUID, question_id: UUID, patch: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
            return self.service.update_question(db, question_id, patch)

        @self.router.delete("/{exam_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete question")
        async def delete_question(exam_id: UUID, question_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
            self.service.delete_question(db, question_id)
            return None

        # --- Ендпойнти для варіантів відповіді на питання ---
        @self.router.post("/{exam_id}/questions/{question_id}/options", status_code=status.HTTP_201_CREATED, summary="Create option for question")
        async def create_option(exam_id: UUID, question_id: UUID, payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
            return self.service.create_option(db, question_id, payload)

        @self.router.patch("/{exam_id}/questions/{question_id}/options/{option_id}", summary="Update option")
        async def update_option(exam_id: UUID, question_id: UUID, option_id: UUID, patch: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
            return self.service.update_option(db, option_id, patch)

        @self.router.delete("/{exam_id}/questions/{question_id}/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete option")
        async def delete_option(exam_id: UUID, question_id: UUID, option_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
            self.service.delete_option(db, option_id)
            return None

        # --- Ендпойнти для журналу іспиту ---
        @self.router.get(
            "",
            response_model=CourseExamsPage,
            summary="Список іспитів для курсу (лише для викладача)",
        )
        async def list_course_exams(
            course_id: UUID = Query(..., description="ID курсу для фільтрації іспитів"),
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Цей функціонал доступний лише для викладачів",
                )
            return self.service.get_exams_for_course(db, course_id)
        
        @self.router.get(
            "/{exam_id}/journal",
            response_model=ExamJournalResponse,
            summary="Отримати журнал іспиту для перевірки (лише для викладача)",
        )
        async def get_exam_journal(
            exam_id: UUID,
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Цей функціонал доступний лише для викладачів",
                )
            return self.journal_service.get_journal_for_exam(db, exam_id)
        