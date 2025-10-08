# API Design Documentation

## Architecture Overview
- **Base URL:** `https://systematics.onrender.com/api`  
- **API Style:** RESTful  
- **Authentication:** JWT Bearer tokens (планується)  
- **Response Format:** JSON  
- **Versioning Strategy:** URL path versioning (`/v1`, `/v2`)  

## Resource Model 

### Exams Resource
- **Endpoint:** `/exams`  
- **Description:** Управління тестами та екзаменами  
- **Attributes:**  
  - `id` (string): Унікальний ідентифікатор  
  - `title` (string): Назва тесту  
  - `description` (string, optional): Опис  
  - `createdBy` (string): ID користувача (викладача), який створив тест  
  - `duration` (number): Час проходження в секундах
- **Relationships:**  
  - Має багато **questions**  
  - Має багато **attempts**     

### Attempts Resource
- **Endpoint:** `/attempts`  
- **Description:** Спроби проходження тестів учнями  
- **Attributes:**  
  - `id` (string): Унікальний ідентифікатор  
  - `examId` (string): Ідентифікатор екзамену  
  - `userId` (string): Ідентифікатор учня  
  - `score` (number, optional): Набрані бали  
  - `startedAt` (datetime): Час початку  
  - `finishedAt` (datetime, optional): Час завершення  
- **Relationships:**  
  - Належить до **exam**  
  - Належить до **user**  

## Design Decisions

### Why Code-First?
Ми обрали підхід **code-first**, бо:    
- Код і документація завжди узгоджені, бо схема OpenAPI генерується автоматично
- Не потрібно вручну підтримувати окремий YAML-файл або синхронізувати зміни
- Зручно змінювати логіку API, не хвилюючись про оновлення документації вручну
- FastAPI автоматично описує моделі з Pydantic у документації

### Pagination Strategy
- Використовуємо **offset-based pagination** для списків (`exams`, `users`, `attempts`)  
- **Default limit:** 10 
- **Minimum limit:** 1
- **Maximum limit:** 100  
- Параметр **offset** визначає кількість елементів, які потрібно пропустити перед вибіркою
- Повертається **metadata** з `total` count та `hasMore`  

### Error Handling
- Єдина та послідовна структура форматів помилок
- Зрозумілі повідомлення, орієнтовані на користувача
- Помилки валідації містять детальну інформацію про поля, що не пройшли перевірку