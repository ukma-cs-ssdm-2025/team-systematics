| № | RTM ID / TC ID | User Story | Компонент / функція | Рівень тесту | Тип (позитивний/негативний) | Тест-кейс | Очікуваний результат | Файл тесту | Власник |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| 1 | TC-001 | US-001 | Analytics / get_group_analytics | Integration | Позитивний | Студент переглядає «Мій атестат» із даними про усі тести та курси | 200 OK, сторінка завантажується за ≤2 с з усіма даними про тести, відображається коректно у Chrome та Firefox | test_analytics.py | SlavaKolinko |
| 2 | TC-002 | US-001 | Analytics / access_control | Unit | Негативний | Спроба доступу до атестату іншого студента | 403 Forbidden, студент НЕ може отримати дані іншого користувача | test_analytics.py | SlavaKolinko |
| 3 | TC-005 | US-003 | CoursesController / access_control | Unit | Негативний | Перевірка доступу наглядача до даних курсів | 403 Forbidden для користувачів без ролі наглядача | test_courses.py | SlavaKolinko |
| 4 | TC-006 | US-003 | CoursesController / compatibility | Non-functional | Позитивний | Перевірка коректного відображення даних курсів у Chrome та Firefox | 200 OK, сторінка працює без критичних помилок у обох браузерах | test_courses.py | SlavaKolinko |
| 5 | TC-007 | US-004 | CoursesController / list_courses | Integration | Позитивний | Студент бачить список своїх майбутніх іспитів | 200 OK, список відображається повністю, дані залишаються після перезавантаження | test_courses.py | SlavaKolinko |
| 6 | TC-008 | US-004 | CoursesController / compatibility | Non-functional | Позитивний | Перевірка сторінки списку іспитів у Chrome та Firefox | 200 OK, інтерфейс коректно працює у обох браузерах | test_courses.py | SlavaKolinko |
| 7 | TC-009 | US-005 | ExamsController / student_responses | Integration | Позитивний | Викладач бачить усі відповіді студентів під час тесту | Відповіді відображаються, автоматично оновлюються і зберігаються, коректно у Chrome та Firefox | test_exams.py, test_attempts.py | SlavaKolinko |
| 8 | TC-010 | US-005 | ExamsController / access_control | Unit | Негативний | Доступ до відповідей студентів для неавторизованих користувачів | 403 Forbidden для користувачів без ролі викладача | test_exams.py | SlavaKolinko |
| 9 | TC-011 | US-006 | ExamsController / extra_time | Integration | Позитивний | Наглядач додає час на тестування для студента | Таймер оновлюється у інтерфейсі студента, зміна зберігається в системі | test_exams.py | SlavaKolinko |
| 10 | TC-012 | US-006 | AttemptService / data_persistence | Unit | Позитивний | Перевірка збереження відповідей студента після додавання часу | Відповіді залишаються збереженими, не втрачаються при розширенні часу | test_attempts.py | SlavaKolinko |
| 11 | TC-013 | US-007 | ExamsController / timer | Integration | Позитивний | Студент бачить таймер з залишком часу під час іспиту | Таймер відображається, кнопка «Завершити» доступна на останньому питанні, коректно у Chrome та Firefox | test_exams.py | SlavaKolinko |
| 12 | TC-014 | US-007 | ExamsController / auto_submit | Integration | Позитивний | Система автоматично завершує іспит після витікання часу | Відповіді автоматично зберігаються, іспит завершується без втрати даних | test_attempts.py | SlavaKolinko |
| 13 | TC-015 | US-008 | ExamsController / question_types | Integration | Позитивний | Викладач створює іспит з відкритими та закритими питаннями | Іспит зберігається і відображається без помилок у Chrome та Firefox | test_questions.py, test_exams.py | SlavaKolinko |
| 14 | TC-016 | US-008 | ExamsController / compatibility | Non-functional | Позитивний | Інтерфейс створення іспитів коректно працює у Chrome та Firefox | 200 OK, всі елементи управління доступні і функціональні | test_exams.py | SlavaKolinko |
| 15 | TC-021 | US-011 | AnalyticsController / group_analytics | Integration | Позитивний | Викладач бачить аналітику результатів групи з графіками | Дані і графіки відображаються повністю, залишаються після перезавантаження | test_analytics.py | SlavaKolinko |
| 16 | TC-022 | US-011 | AnalyticsController / compatibility | Non-functional | Позитивний | Сторінка аналітики працює без критичних помилок у Chrome та Firefox | 200 OK, всі елементи та графіки функціональні | test_analytics.py | SlavaKolinko |

## Тести безпеки та аутентифікації

| № | RTM ID / TC ID | User Story | Компонент / функція | Рівень тесту | Тип (позитивний/негативний) | Тест-кейс | Очікуваний результат | Файл тесту | Власник |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| 17 | SEC-001 | - | AuthService / login_success | Unit | Позитивний | Логін з валідним email та паролем | Повертає JWT-токен з type="bearer" та інформацією про ролі користувача | test_authentication.py | SlavaKolinko |
| 18 | SEC-001 | - | AuthService / login_invalid_password | Unit | Негативний | Спроба логіну з невірним паролем | HTTPException 401 з деталлю "Invalid credentials", пароль перевіряється через bcrypt | test_authentication.py | SlavaKolinko |
| 19 | SEC-001 | - | AuthService / login_invalid_email | Unit | Негативний | Спроба логіну з неіснуючим email | HTTPException 401, користувач не знайдено | test_authentication.py | SlavaKolinko |
| 20 | SEC-002 | - | AuthService / session_timeout | Integration | Негативний | Перевірка автоматичного завершення сесії після 25 хвилин | Токен стає недійсним, наступний запит повертає 401 Unauthorized | test_authentication.py | SlavaKolinko |
| 21 | SEC-002 | - | AuthService / password_hashing | Unit | Позитивний | Перевірка хешування паролів bcrypt | Пароль хешується, verify_password повертає True для правильного пароля | test_hashing_utils.py | SlavaKolinko |
| 22 | SEC-003 | - | AuthService / access_control | Unit | Негативний | Спроба доступу до чужих даних без авторизації | 403 Forbidden для операцій без JWT-токена | test_authentication.py, test_error_handling.py | SlavaKolinko |

## Тести надійності

| № | RTM ID / TC ID | User Story | Компонент / функція | Рівень тесту | Тип (позитивний/негативний) | Тест-кейс | Очікуваний результат | Файл тесту | Власник |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| 23 | REL-001 | - | AttemptService / auto_save | Integration | Позитивний | Автозбереження відповідей студента після кожної відповіді | Відповіді зберігаються у localStorage та БД, не втрачаються при збої | test_attempts.py | SlavaKolinko |
| 24 | REL-001 | - | AttemptService / data_recovery | Unit | Позитивний | Восстановлення стану сесії після перезапуску при збої | Дані студента відновлюються з БД, прогрес не втрачається | test_attempts.py | SlavaKolinko |
| 25 | REL-002 | - | AttemptService / insert_only_model | Unit | Позитивний | Перевірка INSERT-only моделі у БД (не перезаписування) | Відповіді не перезаписуються, кожна версія зберігається | test_attempts.py | SlavaKolinko |
| 26 | REL-001 | - | ExamsController / data_persistence | Integration | Позитивний | Дані іспитів залишаються доступними після перезавантаження | Всі дані зберігаються в БД, не втрачаються | test_exams.py | SlavaKolinko |
| 27 | REL-002 | - | ExamParticipantsService / concurrent_updates | Integration | Позитивний | Синхронізація даних при одночасному оновленні учасників | Дані залишаються консистентними без конфліктів | test_exams.py | SlavaKolinko |
| 28 | ERR-HANDLING | - | ErrorHandling / database_failure | Integration | Негативний | Обробка помилки при відмові БД | Система повертає 500 Internal Server Error, данні не корумпуються | test_error_handling.py, reliability_tests/ | SlavaKolinko |
| 29 | BOUNDARY | - | ExamsService / validation | Unit | Негативний | Перевірка валідації (end_at < start_at) | Система повертає 422 Unprocessable Entity | reliability_tests/test_boundary.py | SlavaKolinko |

## Інші тести

| № | RTM ID / TC ID | User Story | Компонент / функція | Рівень тесту | Тип (позитивний/негативний) | Тест-кейс | Очікуваний результат | Файл тесту | Власник |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| 30 | MODEL-TEST | - | User Model | Unit | Позитивний | Тестування моделі User із усіма полями | Модель коректно валідує всі поля | test_models.py | SlavaKolinko |
| 31 | MODEL-TEST | - | Exam Model | Unit | Позитивний | Тестування моделі Exam із зв'язками | Модель має коректні зв'язки з Course та Question | test_models.py | SlavaKolinko |
| 32 | SCHEMA-TEST | - | ExamSchema Validation | Unit | Позитивний | Валідація Pydantic schema для Exam | Schema правильно валідує поля datetime | test_schema_validators.py | SlavaKolinko |
| 33 | DEPENDENCY-TEST | - | Service Dependencies | Unit | Позитивний | Тестування dependency injection для сервісів | Всі залежності правильно інжектуються | test_dependencies.py | SlavaKolinko |
| 34 | UTIL-TEST | - | Password Hashing | Unit | Позитивний | Тестування утиліт хешування паролів | Пароль коректно хешується та верифікується | test_hashing_utils.py | SlavaKolinko |
| 35 | UTIL-TEST | - | Datetime Utilities | Unit | Позитивний | Тестування утиліт роботи з датами | Конвертація та форматування працює коректно | test_datetime_utils.py | SlavaKolinko |
| 36 | QUESTION-TEST | - | Question Management | Unit | Позитивний | CRUD операції для питань | Створення, читання, оновлення, видалення питань працюють | test_questions.py | SlavaKolinko |
| 37 | ATTEMPT-TEST | - | Attempt Management | Integration | Позитивний | CRUD операції для спроб пройти іспит | Спроби коректно створюються, зберігаються, подаються | test_attempts.py | SlavaKolinko |
| 38 | DATABASE-TEST | - | Database Connection | Unit | Позитивний | Тестування конфігурації та підключення БД | Подключення встановлюється коректно | test_database_and_config.py | SlavaKolinko |
