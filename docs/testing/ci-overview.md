# CI Overview

## Workflow: Run Api Tests
**Файл:** `.github/workflows/run-api-test.yml`  
**Автор пайплайна:** allyxandraaa  
**Призначення:** автоматичне тестування бекенду.

Пайплайн запускається автоматично:
- при кожному **push** у `main`;
- при **pull request** у `main`.

**Основні кроки:**
1. Завантажує репозиторій (checkout).
2. Налаштовує Python 3.11.
3. Встановлює всі залежності (`requirements.txt`).
4. Запускає тести через `pytest`.

**Поточний стан:**
- Workflow стабільно запускається при кожному коміті.  
- CI інтеграція працює правильно.
- Використовує оптимізовану стратегію з розділенням на швидкі unit тести (без ML) та повільніші ML тести (тільки на main).
- Проблеми з сумісністю JSONB/SQLite вирішено через функцію `get_json_type()`.  


## Додаткові воркфлоу
У репозиторії також налаштовано:
- **Run API Tests** (`run-api-test.yml`) — автоматичне тестування API з розділенням на unit тести (швидкі) та ML тести (повільніші);
- **Generate and Auto-Merge API Docs** (`generate-docs.yml`) — автоматична генерація OpenAPI документації з бейджиком статусу в README;
- **Deploy Docs to GitHub Pages** (`deploy-docs.yml`) — деплой документації на GitHub Pages;
- **SonarCloud Analysis** (`sonarcloud.yml`) — статичний аналіз коду;
- **Generate PlantUML Diagrams** (`uml-render.yml`) — створення UML-діаграм з .puml файлів.

**Детальна інформація:** Див. [CI/CD Runbook](/docs/ci-cd/dora-summary.md) для повного опису всіх workflows.


## Quality Gate
Планується (або вже увімкнено) правило:
> “Require status checks to pass before merging”  
Це означає, що код не можна злити в main, якщо тести не проходять.


## Висновок
CI пайплайн **успішно інтегрований**, стабільно працює та автоматично запускає тести.  
Я, як Integration Lead, підтверджую, що:
- тестування повністю інтегроване у CI/CD процес;
- пайплайн регулярно виконується і контролює якість коду.