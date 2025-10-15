[![Open in Codespaces](https://classroom.github.com/assets/launch-codespace-2972f46106e565e64193e422d61a12cf1da4916b45550586e14ef0a7c637dd04.svg)](https://classroom.github.com/open-in-codespaces?assignment_repo_id=20518032)

# Платформа онлайн-іспитів
[![CI Test](https://github.com/ukma-cs-ssdm-2025/team-systematics/actions/workflows/ci-test.yml/badge.svg)](https://github.com/ukma-cs-ssdm-2025/team-systematics/actions/workflows/ci-test.yml)

Розроблений командою _Systematics_, проєкт передбачає розроблення платформи для проведення онлайн-іспитів на базі веб-застосунку, що забезпечує __підтримку різних типів завдань, організацію сесій із обмеженням у часі та інструменти для виявлення плагіату__. Система передбачає ролі студента, викладача та наглядача, надає інструменти для автоматичного оцінювання, формування звітів, контролю доброчесності.

## Інструкції для запуску проекту

### Компіляція Vue проєкту

З директорї client:

```bash
npm run build
```

### Запустити сервер

З кореневої директорії:

```bash
uvicorn src.api.main:app --host 127.0.0.1 --port 3000
```

<hr>

### Запуск серверу Vue для розробки

З директорії client:

```
npm run dev
```


## Наші учасники:
- Малій Олександра - Security Analyst
- Фломбойм Мирослава - Documentation Lead
- Колінько Владислава - Quality Lead
- Бакалина Анастасія - Code Reviewer

## Артефакти:
- [Командний статут](/docs/requirements/TeamCharter.md)
- [Опис проєкту](/docs/requirements/Project-Description.md)
- [Порядок постановки та вирішування завдань](/docs/requirements/ISSUE_WORKFLOW.md)
- [Користувацькі історії](/docs/requirements/user-stories.md)
- [Функціональні і нефункціональні вимоги](/docs/requirements/requirements.md)
- [Матриця простежуваності](/docs/requirements/rtm.md)
<br>
- [Відстеження прогресу](/docs/code-quality/progress.md)
- [Статичний аналіз](/docs/code-quality/static-analysis.md)
- [Огляд коду](/docs/code-quality/review-report.md)

## Архітектура:
- [Архітектурні артефакти](/docs/architecture/)