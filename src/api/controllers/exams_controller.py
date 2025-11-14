from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Query, Path, status, Depends
from uuid import UUID
from src.api.schemas.exams import Exam, ExamCreate, ExamUpdate, ExamsPage, CourseExamsPage, ExamWithQuestions, ExamsResponse
from src.api.schemas.journal import ExamJournalResponse
from src.api.schemas.attempts import Attempt
from src.models.users import User
from src.utils.auth import get_current_user_id, get_current_user, get_current_user_with_role 
from src.api.services.exams_service import ExamsService
from src.api.services.journal_service import JournalService
from .versioning import require_api_version
from src.api.database import get_db
import inspect

class ExamsController:
    def __init__(self, service: ExamsService) -> None:
        self.service = service
        self.journal_service = JournalService()
        self.router = APIRouter(prefix="/exams", tags=["Exams"], dependencies=[Depends(require_api_version)])
        self._register_routes()

    def _register_routes(self):
        """Реєструє всі маршрути для контролера іспитів."""
        self._register_crud_routes()
        self._register_question_routes()
        self._register_option_routes()
        self._register_journal_routes()

    def _register_crud_routes(self):
        """Реєструє CRUD маршрути для іспитів."""
        self._register_list_exams()
        self._register_create_exam()
        self._register_link_exam_to_course()
        self._register_get_exam()
        self._register_get_exam_for_edit()
        self._register_update_exam()
        self._register_publish_exam()
        self._register_delete_exam()
        self._register_start_attempt()

    def _register_question_routes(self):
        """Реєструє маршрути для питань іспиту."""
        self._register_create_question()
        self._register_update_question()
        self._register_delete_question()

    def _register_option_routes(self):
        """Реєструє маршрути для опцій питань."""
        self._register_create_option()
        self._register_update_option()
        self._register_delete_option()

    def _register_journal_routes(self):
        """Реєструє маршрути для журналу іспиту."""
        self._register_list_course_exams()
        self._register_get_exam_journal()

    async def _safe_call(self, fn, *args, **kwargs):
        """Run a function and convert unexpected exceptions to HTTP 500.

        Supports both sync and async callables.
        """
        try:
            result = fn(*args, **kwargs)
            if inspect.isawaitable(result):
                return await result
            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "INTERNAL_ERROR", "message": str(e)},
            )

    def _require_teacher(self, user: User):
        if user.role != 'teacher':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Цей функціонал доступний лише для викладачів",
            )

    def _register_list_exams(self):
        """Реєструє маршрут для списку іспитів."""
        @self.router.get("", response_model=ExamsResponse, summary="List exams")
        async def list_exams(
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
            limit: int = Query(10, ge=1, le=100),
            offset: int = Query(0, ge=0)
        ):
            # Перевірка ролі: тільки студенти можуть переглядати список іспитів
            if current_user.role != 'student':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Доступ до списку іспитів дозволений тільки студентам"
                )
            try:
                result = self.service.list(db, user_id=current_user.id, limit=limit, offset=offset)
                return ExamsResponse(**result)
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

    def _register_create_exam(self):
        """Реєструє маршрут для створення іспиту."""
        @self.router.post("", response_model=Exam, status_code=status.HTTP_201_CREATED, summary="Create exam")
        async def create_exam(
            payload: ExamCreate, 
            db: Session = Depends(get_db), 
            current_user: User = Depends(get_current_user_with_role)
        ):
            # Перевірка ролі: тільки вчитель може створювати іспити
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Тільки вчителі можуть створювати іспити"
                )
            try:
                # Встановлюємо owner_id з поточного користувача
                return self.service.create(db, payload, owner_id=current_user.id)
            except HTTPException as he:
                raise he
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"code": "INTERNAL_ERROR", "message": str(e)}
                )

    def _register_link_exam_to_course(self):
        """Реєструє маршрут для зв'язування іспиту з курсом."""
        @self.router.post("/{exam_id}/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Link exam to course")
        async def link_exam_to_course(
            exam_id: UUID = Path(...),
            course_id: UUID = Path(...),
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role)
        ):
            # Перевірка ролі: тільки вчитель може зв'язувати іспити з курсами
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Тільки вчителі можуть зв'язувати іспити з курсами"
                )
            """Зв'язує екзамен з курсом"""
            self.service.link_to_course(db, exam_id, course_id)
            return None

    def _register_get_exam(self):
        """Реєструє маршрут для отримання іспиту за ID."""
        @self.router.get("/{exam_id}", response_model=Exam, summary="Get exam by id")
        async def get_exam(
            exam_id: UUID, 
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role)
        ):
            # Перевірка ролі: всі автентифіковані користувачі можуть переглядати іспити
            try:
                exam = self.service.get(db, exam_id)
                if not exam:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Exam not found"
                    )
                return exam
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"code": "INTERNAL_ERROR", "message": str(e)}
                )

    def _register_get_exam_for_edit(self):
        """Реєструє маршрут для отримання іспиту для редагування."""
        @self.router.get("/{exam_id}/edit", response_model=ExamWithQuestions, summary="Get exam with questions for editing")
        async def get_exam_for_edit(
            exam_id: UUID = Path(...),
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role)
        ):
            # Перевірка ролі: тільки вчитель може редагувати іспити
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Тільки вчителі можуть редагувати іспити"
                )
            """Отримує іспит з питаннями, опціями та matching_data для редагування"""
            return self.service.get_for_edit(db, exam_id)

    def _register_update_exam(self):
        """Реєструє маршрут для оновлення іспиту."""
        @self.router.patch("/{exam_id}", response_model=Exam, summary="Update exam (partial)")
        async def update_exam(
            patch: ExamUpdate, 
            exam_id: UUID, 
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role)
        ):
            # Перевірка ролі: тільки вчитель може оновлювати іспити
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Тільки вчителі можуть оновлювати іспити"
                )
            return self.service.update(db, exam_id, patch)

    def _register_publish_exam(self):
        """Реєструє маршрут для публікації іспиту."""
        @self.router.post("/{exam_id}/publish", response_model=Exam, summary="Publish exam")
        async def publish_exam(
            exam_id: UUID = Path(...),
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role)
        ):
            # Перевірка ролі: тільки вчитель може публікувати іспити
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Тільки вчителі можуть публікувати іспити"
                )
            """Публікує іспит (змінює статус з draft на published)"""
            return self.service.publish_exam(db, exam_id)

    def _register_delete_exam(self):
        """Реєструє маршрут для видалення іспиту."""
        @self.router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete exam")
        async def delete_exam(
            exam_id: UUID, 
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role)
        ):
            # Перевірка ролі: тільки вчитель може видаляти іспити
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Тільки вчителі можуть видаляти іспити"
                )
            self.service.delete(db, exam_id)
            return None

    def _register_start_attempt(self):
        """Реєструє маршрут для початку спроби іспиту."""
        @self.router.post("/{exam_id}/attempts", response_model=Attempt, status_code=status.HTTP_201_CREATED, summary="Start an attempt for exam")
        async def start_attempt(
            user_id: UUID = Depends(get_current_user_id), 
            exam_id: UUID = Path(...), 
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role)
        ):
            # Перевірка ролі: тільки студент може починати спроби
            if current_user.role != 'student':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Тільки студенти можуть починати спроби"
                )
            return self.service.start_attempt(db, exam_id, user_id)

    def _register_create_question(self):
        """Реєструє маршрут для створення питання."""
        @self.router.post("/{exam_id}/questions", status_code=status.HTTP_201_CREATED, summary="Create question for exam")
        async def create_question(
            exam_id: UUID, 
            payload: dict, 
            db: Session = Depends(get_db), 
            current_user: User = Depends(get_current_user_with_role)
        ):
            # Перевірка ролі: тільки вчитель може створювати питання
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Тільки вчителі можуть створювати питання"
                )
            return self.service.create_question(db, exam_id, payload)

    def _register_update_question(self):
        """Реєструє маршрут для оновлення питання."""
        @self.router.patch("/{exam_id}/questions/{question_id}", summary="Update question")
        async def update_question(
            exam_id: UUID, 
            question_id: UUID, 
            patch: dict, 
            db: Session = Depends(get_db), 
            current_user: User = Depends(get_current_user_with_role)
        ):
            # Перевірка ролі: тільки вчитель може оновлювати питання
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Тільки вчителі можуть оновлювати питання"
                )
            return self.service.update_question(db, question_id, patch)

    def _register_delete_question(self):
        """Реєструє маршрут для видалення питання."""
        @self.router.delete("/{exam_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete question")
        async def delete_question(
            exam_id: UUID, 
            question_id: UUID, 
            db: Session = Depends(get_db), 
            current_user: User = Depends(get_current_user_with_role)
        ):
            # Перевірка ролі: тільки вчитель може видаляти питання
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Тільки вчителі можуть видаляти питання"
                )
            self.service.delete_question(db, question_id)
            return None

    def _register_create_option(self):
        """Реєструє маршрут для створення опції."""
        @self.router.post("/{exam_id}/questions/{question_id}/options", status_code=status.HTTP_201_CREATED, summary="Create option for question")
        async def create_option(
            exam_id: UUID, 
            question_id: UUID, 
            payload: dict, 
            db: Session = Depends(get_db), 
            current_user: User = Depends(get_current_user_with_role)
        ):
            # Перевірка ролі: тільки вчитель може створювати опції
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Тільки вчителі можуть створювати опції"
                )
            return self.service.create_option(db, question_id, payload)

    def _register_update_option(self):
        """Реєструє маршрут для оновлення опції."""
        @self.router.patch("/{exam_id}/questions/{question_id}/options/{option_id}", summary="Update option")
        async def update_option(
            exam_id: UUID, 
            question_id: UUID, 
            option_id: UUID, 
            patch: dict, 
            db: Session = Depends(get_db), 
            current_user: User = Depends(get_current_user_with_role)
        ):
            # Перевірка ролі: тільки вчитель може оновлювати опції
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Тільки вчителі можуть оновлювати опції"
                )
            return self.service.update_option(db, option_id, patch)

    def _register_delete_option(self):
        """Реєструє маршрут для видалення опції."""
        @self.router.delete("/{exam_id}/questions/{question_id}/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete option")
        async def delete_option(
            exam_id: UUID, 
            question_id: UUID, 
            option_id: UUID, 
            db: Session = Depends(get_db), 
            current_user: User = Depends(get_current_user_with_role)
        ):
            # Перевірка ролі: тільки вчитель може видаляти опції
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Тільки вчителі можуть видаляти опції"
                )
            self.service.delete_option(db, option_id)
            return None

    def _register_list_course_exams(self):
        """Реєструє маршрут для списку іспитів курсу."""
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
            self._require_teacher(current_user)
            return await self._safe_call(self.service.get_exams_for_course, db, course_id)

    def _register_get_exam_journal(self):
        """Реєструє маршрут для отримання журналу іспиту."""
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
            self._require_teacher(current_user)
            return await self._safe_call(self.journal_service.get_journal_for_exam, db, exam_id)
        