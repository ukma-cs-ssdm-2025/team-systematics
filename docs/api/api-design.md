# API Design Documentation

## Architecture Overview
- **Base URL:** `https://systematics.onrender.com/api`  
- **API Style:** RESTful  
- **Authentication:** JWT Bearer tokens (планується)  
- **Response Format:** JSON  
- **Versioning Strategy:** Query parameter 

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
  - `max_attempts` (int): Максимальна кількість спроб проходження тесту  
  - `pass_threshold` (int): Мінімальний результат для успішного проходження  
  - `owner_id` (UUID): Ідентифікатор користувача-викладача, який створив тест  
  - `question_count` (int, default=0): Кількість доступних питань у тесті  
- **Relationships:**  
  - Має багато **attempts**    
  
### Attempt Resource
- **Endpoint:** `/attempts`  
- **Description:** Спроба проходження екзамену користувачем  
- **Attributes:**  
  - `id` (UUID): Унікальний ідентифікатор спроби  
  - `exam_id` (UUID): Ідентифікатор екзамену  
  - `user_id` (UUID): Ідентифікатор користувача  
  - `status` (string): Поточний статус спроби: `in_progress` | `submitted` | `expired`  
  - `started_at` (PastDatetime): Дата і час початку спроби  
  - `due_at` (FutureDatetime): Дата і час завершення спроби  
  - `submitted_at` (PastDatetime, optional): Дата і час відправки спроби, якщо завершена  
  - `score_percent` (int, optional, 0–100): Результат у відсотках після оцінювання  
- **Relationships:**  
  - Належить до **exam**    
  - Містить список **answers**    

### Answers Resource
- **Endpoint:** `/answers`  
- **Description:** Відповіді учнів на питання під час проходження тестів  
- **Attributes:**  
  - `id` (UUID): Унікальний ідентифікатор відповіді  
  - `attempt_id` (UUID): Ідентифікатор спроби 
  - `question_id` (UUID): Ідентифікатор питання 
  - `text` (string, optional): Текстова відповідь для питань типу **short-answer**  
  - `selected_option_ids` (List[UUID], optional): Список обраних варіантів для **multiple-choice** питань  
  - `saved_at` (Pastdatetime): Дата і час збереження відповіді 
- **Relationships:**  
  - Належить до **attempt**  

## Design Decisions

### Why Code-First?
Ми обрали підхід **code-first**, бо:    
- Код і документація завжди узгоджені, бо схема OpenAPI генерується автоматично
- Не потрібно вручну підтримувати окремий YAML-файл або синхронізувати зміни
- Зручно змінювати логіку API, не хвилюючись про оновлення документації вручну
- FastAPI автоматично описує моделі з Pydantic у документації

### Pagination Strategy
- Використовуємо **offset-based pagination** для списків `exams`, `users`, `attempts`
- **Default limit:** 10 
- **Minimum limit:** 1
- **Maximum limit:** 100  
- Параметр **offset** визначає кількість елементів, які потрібно пропустити перед вибіркою
- Повертається **metadata** з `total` count та `hasMore`  

### Error Handling
- Єдина та послідовна структура форматів помилок
- Зрозумілі повідомлення, орієнтовані на користувача
- Помилки валідації містять детальну інформацію про поля, що не пройшли перевірку