# API Design Documentation

## Architecture Overview
- **Base URL:** `https://systematics.onrender.com/api`  
- **API Style:** RESTful  
- **Authentication:** JWT Bearer tokens  
- **Response Format:** JSON  
- **Versioning Strategy:** Query parameter `api-version` (default: `1.0`)

## Resource Model 

### Exams Resource
- **Endpoint:** `/exams`  
- **Description:** Управління тестами та екзаменами  
- **Attributes:**  
  - `id` (UUID): Унікальний ідентифікатор тесту  
  - `title` (string): Назва тесту  
  - `instructions` (string, optional): Інструкції для проходження тесту  
  - `start_at` (datetime): Дата і час початку доступності тесту  
  - `end_at` (datetime): Дата і час завершення доступності тесту  
  - `duration_minutes` (int): Тривалість іспиту в хвилинах
  - `max_attempts` (int): Максимальна кількість спроб проходження тесту  
  - `pass_threshold` (int): Мінімальний результат для успішного проходження  
  - `owner_id` (UUID): Ідентифікатор користувача-викладача, який створив тест  
  - `question_count` (int, default=0): Кількість доступних питань у тесті  
  - `status` (string): Статус іспиту: `draft` | `published` | `open` | `closed`
  - `published` (bool): Чи опубліковано іспит
- **Relationships:**  
  - Має багато **attempts**  
  - Має багато **questions**  
  - Пов'язаний з багатьма **courses** через `course_exams`
  
### Attempt Resource
- **Endpoint:** `/attempts`  
- **Description:** Спроба проходження екзамену користувачем  
- **Attributes:**  
  - `id` (UUID): Унікальний ідентифікатор спроби  
  - `exam_id` (UUID): Ідентифікатор екзамену  
  - `user_id` (UUID): Ідентифікатор користувача  
  - `status` (string): Поточний статус спроби: `in_progress` | `submitted` | `expired` | `completed`  
  - `started_at` (PastDatetime): Дата і час початку спроби  
  - `due_at` (datetime): Дата і час завершення спроби  
  - `submitted_at` (PastDatetime, optional): Дата і час відправки спроби, якщо завершена  
  - `score_percent` (int, optional, 0–100): Результат у відсотках після оцінювання  
  - `time_spent_seconds` (int, optional): Час, витрачений на проходження в секундах
- **Relationships:**  
  - Належить до **exam**    
  - Містить список **answers**    
  
### Answers Resource
- **Endpoint:** `/attempts/{attempt_id}/answers`  
- **Description:** Відповіді учнів на питання під час проходження тестів  
- **Attributes:**  
  - `id` (UUID): Унікальний ідентифікатор відповіді  
  - `attempt_id` (UUID): Ідентифікатор спроби 
  - `question_id` (UUID): Ідентифікатор питання 
  - `text` (string, optional): Текстова відповідь для питань типу **short-answer**  
  - `selected_option_ids` (List[UUID], optional): Список обраних варіантів для **multiple-choice** питань  
  - `saved_at` (PastDatetime): Дата і час збереження відповіді 
- **Relationships:**  
  - Належить до **attempt**  

### Courses Resource
- **Endpoint:** `/courses`  
- **Description:** Управління курсами та записом студентів на курси  
- **Attributes:**  
  - `id` (UUID): Унікальний ідентифікатор курсу  
  - `name` (string): Назва курсу  
  - `code` (string): Код курсу (5 символів)
  - `description` (string, optional): Опис курсу  
  - `student_count` (int): Кількість студентів, записаних на курс
  - `exam_count` (int): Кількість іспитів, пов'язаних з курсом
  - `is_enrolled` (bool): Чи записаний поточний користувач на курс
  - `teachers` (List[string]): Список імен викладачів курсу
- **Relationships:**  
  - Має багато **exams** через `course_exams`
  - Має багато **students** через `course_enrollments`
  - Має багато **supervisors** через `course_supervisors`

### Users Resource
- **Endpoint:** `/users`  
- **Description:** Управління профілями користувачів  
- **Attributes:**  
  - `id` (UUID): Унікальний ідентифікатор користувача  
  - `email` (EmailStr): Email адреса користувача
  - `full_name` (string): Повне ім'я користувача
  - `major_name` (string): Назва спеціальності користувача
  - `avatar_url` (HttpUrl, optional): Посилання на аватар користувача
- **Endpoints:**
  - `GET /users/me` - Отримати профіль поточного користувача
  - `GET /users/me/notifications` - Отримати налаштування сповіщень
  - `PUT /users/me/notifications` - Оновити налаштування сповіщень
  - `POST /users/me/avatar` - Завантажити або оновити аватар
  - `GET /users/majors` - Отримати список усіх спеціальностей

### Auth Resource
- **Endpoint:** `/auth`  
- **Description:** Аутентифікація та реєстрація користувачів  
- **Endpoints:**
  - `POST /auth/login` - Вхід користувача (повертає JWT токен)
  - `POST /auth/register` - Реєстрація нового користувача (повертає JWT токен)
- **Response:**  
  - `access_token` (string): JWT токен для авторизації
  - `token_type` (string): Тип токена (завжди "bearer")
  - `user` (UserResponse): Інформація про користувача

### Transcript Resource
- **Endpoint:** `/transcript`  
- **Description:** Отримання атестату з оцінками поточного користувача  
- **Attributes:**  
  - Список завершених іспитів з оцінками та датами проходження

### Exam Participants Resource
- **Endpoint:** `/exam-participants`  
- **Description:** Управління учасниками іспитів (для викладачів)  
- **Endpoints:**
  - `GET /exam-participants` - Список учасників іспитів
  - `POST /exam-participants` - Додати учасника до іспиту
  - `DELETE /exam-participants/{participant_id}` - Видалити учасника з іспиту
  - `PATCH /exam-participants/{participant_id}` - Оновити дані учасника

## Design Decisions

### Why Code-First?
Ми обрали підхід **code-first**, бо:    
- Код і документація завжди узгоджені, бо схема OpenAPI генерується автоматично
- Не потрібно вручну підтримувати окремий YAML-файл або синхронізувати зміни
- Зручно змінювати логіку API, не хвилюючись про оновлення документації вручну
- FastAPI автоматично описує моделі з Pydantic у документації

### Authentication
- Використовується **JWT Bearer tokens** для автентифікації
- Токен передається в заголовку `Authorization: Bearer <token>`
- Токен містить `sub` (user ID) та `roles` (список ролей користувача)
- Ролі: `student`, `teacher`, `supervisor`
- Токен має термін дії, визначений в конфігурації

### Pagination Strategy
- Використовуємо **offset-based pagination** для списків `exams`, `courses`, `users`, `attempts`
- **Default limit:** 10 
- **Minimum limit:** 1
- **Maximum limit:** 100  
- Параметр **offset** визначає кількість елементів, які потрібно пропустити перед вибіркою
- Повертається **metadata** з `total` count, `limit` та `offset`  

### Versioning Strategy
- Версіонування через query parameter `api-version`
- Поточна версія: `1.0` (default)
- Непідтримувані версії повертають помилку 400
- Всі endpoints вимагають параметр версії (через dependency injection)

### Error Handling
- Єдина та послідовна структура форматів помилок
- Зрозумілі повідомлення, орієнтовані на користувача
- Помилки валідації містять детальну інформацію про поля, що не пройшли перевірку
- Стандартні HTTP коди статусів: 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 500 (Internal Server Error)