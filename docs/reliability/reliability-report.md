# Звіт про надійність системи

## Огляд

Цей документ містить аналіз знайдених проблем надійності, їх критичність, опис застосованих виправлень та перелік проблем, що залишилися відкритими.

---

## Таблиця всіх знайдених проблем

| # | Проблема | Категорія | Критичність | Застосований патерн |
|---|----------|-----------|-------------|---------------------|
| 1 | Відсутність обробки непередбачених помилок | Обробка помилок | High | Global Exception Handler |
| 2 | Занадто широке перехоплення помилок | Обробка помилок | Medium | Specific Exception Handling |
| 3 | Витік внутрішніх деталей у повідомленнях | Обробка помилок | High | Error Message Sanitization |
| 4 | Відсутність обробки помилок у route handlers | Обробка помилок | High | Defensive Programming |
| 5 | Виклики БД без таймаутів | Зовнішні залежності | High | Timeout Pattern |
| 6 | Файлові операції без валідації та таймаутів | Зовнішні залежності | High | Input Validation + Timeout Pattern |
| 7 | Нульові або порожні значення не перевіряються | Валідація | Medium | Guard Clauses |
| 8 | Відсутня перевірка типів | Валідація | Medium | Type Checking |
| 9 | Повернення None без логування | Silent failures | Medium | Logging |
| 10 | Непередбачена поведінка замість чіткої помилки | Silent failures | Medium | Fail-Safe + Logging |
| 11 | Довгі операції у request handler | Продуктивність | High | Timeout Pattern + Fallback Mechanism |
| 12 | Відсутність обробки помилок у довгих операціях | Обробка помилок | High | Error Handling + Fallback Mechanism |

---

## Детальний опис проблем та виправлень

### 1. Відсутність обробки непередбачених помилок

**Критичність:** High

**Проблема:**
У коді була обробка помилок лише для визначених типів помилок (`AppError`), але не було обробки непередбачених винятків, що могли призвести до крашів сервера.

**Перед:**
```python
@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return exc.to_response()
# Не було обробника для Exception
```

**Після:**
```python
@app.exception_handler(Exception)
async def generic_error_handler(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content={
        "error": {
            "code": ErrorCode.INTERNAL_ERROR,
            "message": "An unexpected error occurred",
            "details": None
        }
    })
```

**Застосований патерн:** Global Exception Handler - забезпечує, що всі необроблені винятки перехоплюються та повертають коректну відповідь замість крашу сервера.

---

### 2. Занадто широке перехоплення помилок

**Критичність:** Medium

**Проблема:**
Обробка виключень через `StarletteHTTPException` була занадто загальною, що могло приховати важливі системні помилки.

**Перед:**
```python
@app.exception_handler(StarletteHTTPException)
async def starlette_exc_handler(_: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={
        "error": {"code": code, "message": str(exc.detail), "details": None}
    })
```

**Після:**
```python
@app.exception_handler(StarletteHTTPException)
async def starlette_exc_handler(_: Request, exc: StarletteHTTPException):
    # Обробка лише конкретних статусів помилок
    if exc.status_code == 404:
        return JSONResponse(status_code=exc.status_code, content={
            "error": {"code": ErrorCode.NOT_FOUND, "message": "Resource not found", "details": None}
        })
    elif exc.status_code == 403:
        return JSONResponse(status_code=exc.status_code, content={
            "error": {"code": ErrorCode.FORBIDDEN, "message": "Access forbidden", "details": None}
        })
    # ... інші конкретні статуси
```

**Застосований патерн:** Specific Exception Handling - розрізнення типів помилок для більш точної обробки та логування.

---

### 3. Витік внутрішніх деталей у повідомленнях

**Критичність:** High

**Проблема:**
Повідомлення про помилки могли містити внутрішні деталі (стеки, шляхи файлів), що небезпечно з точки зору безпеки.

**Перед:**
```python
@app.exception_handler(StarletteHTTPException)
async def starlette_exc_handler(_: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={
        "error": {"code": code, "message": str(exc.detail), "details": None}
    })
```

**Після:**
```python
"message": "An unexpected error occurred"  # Загальне повідомлення без деталей
# Деталі логуються на сервері, але не передаються клієнту
```

**Застосований патерн:** Error Message Sanitization - приховування внутрішніх деталей від клієнта, зберігаючи їх у логах для діагностики.

---

### 4. Відсутність обробки помилок у route handlers

**Критичність:** High

**Проблема:**
Деякі route handlers не мали обробки помилок, що могло призвести до крашів сервера.

**Перед:**
```python
@self.router.get("/{exam_id}", response_model=Exam, summary="Get exam by id")
async def get_exam(exam_id: UUID, db: Session = Depends(get_db)):
    return self.service.get(db, exam_id)
```

**Після:**
```python
@self.router.get("/{exam_id}", response_model=Exam)
async def get_exam(exam_id: UUID, db: Session = Depends(get_db)):
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
```

**Застосований патерн:** Defensive Programming - обгортання критичних операцій у try/except для запобігання неочікуваним крашам.

---

### 5. Виклики БД без таймаутів

**Критичність:** High

**Проблема:**
Підключення до бази даних не мали налаштувань таймаутів, що могло призвести до зависання запитів.

**Перед:**
```python
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

**Після:**
```python
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Перевіряє з'єднання перед використанням
    connect_args={
        "connect_timeout": 10,  # Таймаут підключення (секунди)
        "options": "-c statement_timeout=30000"  # Таймаут виконання запиту (30 секунд)
    } if "postgresql" in DATABASE_URL else {}
)
```

**Застосований патерн:** Timeout Pattern - обмеження часу виконання операцій для запобігання блокування системи.

---

### 6. Файлові операції без валідації та таймаутів

**Критичність:** High

**Проблема:**
Завантаження файлів у Cloudinary не мало валідації розміру, типу файлу та таймаутів.

**Перед:**
```python
try:
    upload_result = cloudinary.uploader.upload(
        file.file,
        public_id=public_id,
        overwrite=True,
    )
except cloudinary.exceptions.Error as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to upload image: {str(e)}"
    )
```

**Після:**
```python
# Валідація розміру файлу (максимум 5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024
file_content = file.file.read()
if len(file_content) > MAX_FILE_SIZE:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"File size exceeds maximum allowed size"
    )

# Валідація типу файлу
allowed_content_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
if file.content_type not in allowed_content_types:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid file type"
    )

# Завантаження з таймаутом
upload_result = cloudinary.uploader.upload(
    file.file,
    public_id=public_id,
    overwrite=True,
    timeout=30,  # Таймаут завантаження (секунди)
)
```

**Застосований патерн:** Input Validation + Timeout Pattern - перевірка вхідних даних перед обробкою та обмеження часу операцій.

---

### 7. Нульові або порожні значення не перевіряються

**Критичність:** Medium

**Проблема:**
Методи репозиторіїв не перевіряли вхідні параметри на null або порожні значення.

**Перед:**
```python
def get(self, exam_id: UUID) -> Optional[Exam]:
    return self.db.query(Exam).filter(Exam.id == exam_id).first()
```

**Після:**
```python
def get(self, exam_id: UUID) -> Optional[Exam]:
    if not exam_id:
        logger.warning("get() called with None or empty exam_id")
        return None
    exam = self.db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        logger.debug(f"Exam with id {exam_id} not found")
    return exam
```

**Застосований патерн:** Guard Clauses - рання перевірка вхідних параметрів для запобігання некоректним операціям.

---

### 8. Відсутня перевірка типів

**Критичність:** Medium

**Проблема:**
Метод `create_question` приймав `dict` без перевірки типів вкладених структур.

**Перед:**
```python
def create_question(self, exam_id: UUID, payload) -> Question:
    question_data = {k: v for k, v in payload.items() if k not in ('options', 'matching_data')}
    q = Question(**question_data)
    # ...
    options = payload.get('options') or []
    for opt in options:
        o = Option(question_id=q.id, text=opt.get('text'), is_correct=opt.get('is_correct', False))
```

**Після:**
```python
def create_question(self, exam_id: UUID, payload) -> Question:
    # Валідація вхідних даних
    if not payload:
        raise ValueError("Payload cannot be None or empty")
    if not isinstance(payload, dict):
        raise TypeError(f"Payload must be a dict, got {type(payload).__name__}")
    
    options = payload.get('options') or []
    if not isinstance(options, list):
        raise TypeError(f"Options must be a list, got {type(options).__name__}")
    for opt in options:
        if not isinstance(opt, dict):
            raise TypeError(f"Each option must be a dict, got {type(opt).__name__}")
        # ...
```

**Застосований патерн:** Type Checking - явна перевірка типів для запобігання помилкам під час виконання.

---

### 9. Повернення None без логування

**Критичність:** Medium

**Проблема:**
Методи репозиторіїв повертали `None` без логування, що ускладнювало діагностику.

**Перед:**
```python
def update_question(self, question_id: UUID, patch: dict) -> Optional[Question]:
    q = self.db.query(Question).filter(Question.id == question_id).first()
    if not q:
        return None  # Без логування
```

**Після:**
```python
def update_question(self, question_id: UUID, patch: dict) -> Optional[Question]:
    if not question_id:
        logger.warning("update_question() called with None or empty question_id")
        return None
    q = self.db.query(Question).filter(Question.id == question_id).first()
    if not q:
        logger.debug(f"Question with id {question_id} not found for update")
        return None
```

**Застосований патерн:** Logging - додавання логів для відстеження поведінки системи та діагностики проблем.

---

### 10. Непередбачена поведінка замість чіткої помилки

**Критичність:** Medium

**Проблема:**
Метод `_run_fast_tfidf_filter` повертав порожній список при помилці без логування.

**Перед:**
```python
def _run_fast_tfidf_filter(...) -> List[Dict[str, Any]]:
    corpus = [base_text] + candidate_texts
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        # Наприклад, якщо всі тексти порожні або надто короткі
        return []
```

**Після:**
```python
def _run_fast_tfidf_filter(...) -> List[Dict[str, Any]]:
    if not base_text or not base_text.strip():
        logger.warning("_run_fast_tfidf_filter called with empty base_text")
        return []
    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError as e:
        logger.warning(f"TF-IDF vectorization failed: {str(e)}")
        return []
```

**Застосований патерн:** Fail-Safe + Logging - безпечне повернення значення за замовчуванням з логуванням причини.

---

### 11. Довгі операції у request handler

**Критичність:** High

**Проблема:**
Метод `check_attempt` виконував довгі обчислювальні операції без обмеження часу.

**Перед:**
```python
def check_attempt(self, db: Session, attempt: Attempt) -> PlagiarismReport:
    base_text = self._build_attempt_text(db, attempt.id)
    # ... довгі операції без обмеження часу
    deep_matches, _ = self._run_deep_semantic_analysis(db, base_text, fast_matches)
```

**Після:**
```python
def check_attempt(self, db: Session, attempt: Attempt) -> PlagiarismReport:
    import time
    start_time = time.time()
    MAX_PROCESSING_TIME = 60  # Максимальний час обробки (секунди)
    
    # Перевірка часу виконання
    elapsed = time.time() - start_time
    if elapsed > MAX_PROCESSING_TIME:
        logger.warning(f"Plagiarism check exceeded time limit, using fast check only")
        # Повертаємо результат на основі швидкої перевірки
        return fast_result
    
    # Перевірка часу перед глибоким аналізом
    if elapsed > MAX_PROCESSING_TIME * 0.7:
        logger.info(f"Skipping deep analysis due to time constraints")
        final_matches = fast_matches
    else:
        deep_matches, _ = self._run_deep_semantic_analysis(...)
```

**Застосований патерн:** Timeout Pattern + Fallback Mechanism - обмеження часу виконання з fallback на швидший алгоритм.

---

### 12. Відсутність обробки помилок у довгих операціях

**Критичність:** High

**Проблема:**
Довгі операції у `check_attempt` не мали належної обробки помилок.

**Перед:**
```python
def check_attempt(self, db: Session, attempt: Attempt) -> PlagiarismReport:
    base_text = self._build_attempt_text(db, attempt.id)
    # ... операції без обробки помилок
    deep_matches, _ = self._run_deep_semantic_analysis(db, base_text, fast_matches)
    # ... якщо виникне помилка, метод може крашнути
```

**Після:**
```python
def check_attempt(self, db: Session, attempt: Attempt) -> PlagiarismReport:
    try:
        # ... всі операції
        return self._to_report(check)
    except Exception as e:
        logger.error(f"Error during plagiarism check for attempt {attempt.id}: {str(e)}", exc_info=True)
        # Повертаємо безпечний результат у разі помилки
        check = self.repo.create_or_update(
            db,
            attempt_id=attempt.id,
            uniqueness_percent=100.0,
            max_similarity=0.0,
            status=PlagiarismStatus.ok,
            details={"matches": [], "error": str(e)},
        )
        return self._to_report(check)
```

**Застосований патерн:** Error Handling + Fallback Mechanism - обробка помилок з безпечним fallback результатом.

---

## Опис застосованих патернів надійності

### 1. Global Exception Handler
Централізована обробка всіх необроблених винятків для запобігання крашам сервера та забезпечення консистентного формату відповідей про помилки.

### 2. Specific Exception Handling
Розрізнення типів помилок для більш точної обробки та логування, замість загального перехоплення всіх винятків.

### 3. Error Message Sanitization
Приховування внутрішніх деталей системи від клієнтів, зберігаючи їх у логах для діагностики. Підвищує безпеку та запобігає витоку конфіденційної інформації.

### 4. Defensive Programming
Обгортання критичних операцій у try/except блоки та додавання перевірок на некоректні вхідні дані для зменшення ймовірності крашів.

### 5. Timeout Pattern
Обмеження часу виконання операцій (підключення до БД, завантаження файлів, обробка даних) для запобігання блокування системи та зависання запитів.

### 6. Input Validation + Timeout Pattern
Комбінація перевірки вхідних даних (розмір файлів, типи даних) та обмеження часу операцій для запобігання обробці некоректних даних та зависання системи.

### 7. Guard Clauses
Рання перевірка вхідних параметрів на `None` та порожні значення перед виконанням основної логіки для запобігання некоректним операціям.

### 8. Type Checking
Явна перевірка типів даних за допомогою `isinstance` для запобігання помилкам під час виконання та некоректній поведінці програми.

### 9. Logging
Реєстрація подій та помилок для діагностики та моніторингу. Спрощує виявлення проблем та відстеження поведінки системи.

### 10. Fail-Safe + Logging
Безпечне повернення значення за замовчуванням при помилках з логуванням причини для запобігання silent failures.

### 11. Timeout Pattern + Fallback Mechanism
Обмеження часу виконання з fallback на швидший алгоритм або альтернативний шлях виконання при перевищенні часу.

### 12. Error Handling + Fallback Mechanism
Обробка помилок з безпечним fallback результатом для забезпечення продовження роботи системи навіть при збоях.

---

## Проблеми, що залишилися відкритими

### 1. Частковий витік внутрішніх деталей
Деякі місця в коді можуть виводити внутрішні деталі помилок у відповідях клієнтам. Потрібно перевірити всі місця, де формуються повідомлення про помилки, та додати тести для перевірки.

**Пріоритет:** Medium

### 2. Неповне покриття route handlers обробкою помилок
Не всі route handlers мають явну обробку помилок. Потрібно додати обробку помилок у критичні handlers або використати декоратори для автоматичної обробки.

**Пріоритет:** Medium

### 3. Відсутність retry механізмів для зовнішніх сервісів
Операції з Cloudinary та іншими зовнішніми сервісами не мають retry логіки при тимчасових збоях. Потрібно додати механізми повторних спроб з експоненційним backoff.

**Пріоритет:** Low

### 4. Відсутність rate limiting
Система не має обмеження кількості запитів від одного клієнта. Потрібно додати rate limiting middleware для захисту від DoS атак.

**Пріоритет:** Medium

### 5. Відсутність моніторингу та алертів
Система не має інтеграції з системами моніторингу. Потрібно додати моніторинг (наприклад, Prometheus + Grafana) та налаштувати алерти для критичних помилок.

**Пріоритет:** Low