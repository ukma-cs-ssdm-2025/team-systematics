[![Open in Codespaces](https://classroom.github.com/assets/launch-codespace-2972f46106e565e64193e422d61a12cf1da4916b45550586e14ef0a7c637dd04.svg)](https://classroom.github.com/open-in-codespaces?assignment_repo_id=20518032)

# Платформа онлайн-іспитів
[![CI Test](https://github.com/ukma-cs-ssdm-2025/team-systematics/actions/workflows/ci-test.yml/badge.svg)](https://github.com/ukma-cs-ssdm-2025/team-systematics/actions/workflows/ci-test.yml)

Розроблений командою _Systematics_, проєкт передбачає створення платформи для проведення онлайн-іспитів на базі веб-застосунку, що забезпечує __підтримку різних типів завдань, організацію сесій із обмеженням у часі та інструменти для виявлення плагіату__. Система передбачає ролі студента, викладача та наглядача, надає інструменти для автоматичного оцінювання, формування звітів, контролю доброчесності.

## Наші учасники:
| Прізвище Ім'я           | GitHub                                                 | Ролі
| ----------------------- | ------------------------------------------------------ |---------------------|
| Малій Олександра        | [@allyxandraaa](https://github.com/allyxandraaa)       | Debugger            |
| Фломбойм Мирослава      | [@MyroslavaFlom](https://github.com/MyroslavaFlom)     | QA Planner          |
| Колінько Владислава     | [@SlavaKolinko](https://github.com/SlavaKolinko)       | Test Lead           |
| Бакалина Анастасія      | [@bakalynaa](https://github.com/bakalynaa)             | Integration Lead    |

## Артефакти вимог:
- [Командний статут](/TeamCharter.md)

**Документація API**
- [API документація дизайну](/docs/api/api-design.md)
- [Автоматично згенерований OpenAPI spec](/docs/api/openapi-generated.yaml)
- [API атрибути якості](/docs/api/quality-attributes.md)

**Архітектура:**
- [Високорівнева архітектура](docs/architecture/high-level-design.md)
- [Матриця простежуваності вимог](/docs/architecture/traceability-matrix.md)

- 1.1 UML-діаграми
   - [Діаграма діяльності](/docs/architecture/uml/Activity_diagram.puml)     | [Picture](/docs/architecture/uml/uml-preview/Activity_diagram_preview.md)
   - [Діаграма компонентів](/docs/architecture/uml/Component_diagram.puml)   | [Picture](/docs/architecture/uml/uml-preview/Component_diagram_preview.md)
   - [Діаграма розгортання](/docs/architecture/uml/Deployment_diagram.puml)  | [Picture](/docs/architecture/uml/uml-preview/Deployment_diagram.md)
   - [Діаграма послідовності](/docs/architecture/uml/Sequence_diagram.puml)  | [Picture](/docs/architecture/uml/uml-preview/Sequence_diagram.md)

- 1.2 Architecture Decision Records
   - [ADR-001](/docs/architecture/ADR-001.md)
   - [ADR-002](/docs/architecture/ADR-002.md)
   - [ADR-003](/docs/architecture/ADR-003.md)

 **Якість коду**
 - [Прогрес розробки](/docs/code-quality/progress.md)
 - [Рев'ю коду](/docs/code-quality/review-report.md)
 - [Статичний аналіз бекенду](/docs/code-quality/static-analysis.md)

 **Вимоги**
 - [Порядок постановки та вирішування завдань](/docs/requirements/ISSUE_WORKFLOW.md)
 - [Опис проєкту](/docs/requirements/Project-Description.md)
 - [Функціональні і нефункціональні вимоги](/docs/requirements/requirements.md)
 - [Матриця простежуваності (RTM)](/docs/requirements/rtm.md)
 - [Користувацькі історії](/docs/requirements/user-stories.md)

 **Тестування**
 - [CI Overview](/docs/testing/ci-overview.md)
 - [Журнал дебагінгу](/docs/testing/debugging-log.md)
 - [Стратегія Тестування](/docs/testing/testing-strategy.md)
 - [Покриття тестами](/docs/testing/coverage.txt)

 **Валідація**
 - [Тест план](/docs/validation/test-plan.md)
 - [Рев'ю іншої команди](/docs/validation/review-log.md)


 **Відео-звіти у Loom**
 - [Loom](/Loom)


## Розгорнутий у мережі проєкт:

Наш проєкт розгорнуто на платформі Render і доступний для перегляду.

[https://systematics-exams-server.onrender.com/](https://systematics-exams-server.onrender.com/)

**⚠️ Будь ласка, зауважте:** Додаток розміщено на безкоштовному тарифі, тому **перше завантаження може тривати до 50 секунд**, поки сервер "прокидається" після періоду бездіяльності. Подальша робота буде швидкою.


## Інструкції для локального запуску проекту
### Передумови
- Встановити [Docker Desctop](https://www.docker.com/products/docker-desktop/)

### 0. Клонувати репозиторій
```bash
git clone https://github.com/ukma-cs-ssdm-2025/team-systematics.git
cd team-systematics
```
### 1. Створити файл .env
```bash
DB_USER=postgres
DB_PASSWORD=3xzw48Y7IrIw2WgW
DB_NAME=Systematics
DB_HOST=db
DB_PORT=5432

POSTGRES_DB=${DB_NAME}
POSTGRES_USER=${DB_USER}
POSTGRES_PASSWORD=${DB_PASSWORD}
```

### 2. Активувати  віртуальне середовище Python
```bash
source venv/bin/activate  # для Mac/Linux
venv\Scripts\activate     # для Windows
```

### 2. Запустити докер 
```bash
docker compose up --build
```

### 3. Запустити сервер за посиланням
```bash
http://localhost:3000/
```
