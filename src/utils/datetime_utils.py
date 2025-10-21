from datetime import datetime, timezone
from typing import Optional


def to_utc_iso(dt: Optional[datetime]) -> Optional[str]:
    """Перетворює об'єкт datetime у UTC ISO 8601 рядок.

    Ця функція приймає об'єкт datetime, який може бути як "наївним"
    (naive, без інформації про часову зону), так і "обізнаним" (aware,
    з часовою зоною). Вона гарантує, що дата і час будуть коректно
    конвертовані в часову зону UTC, а потім форматує їх у стандартний
    рядок ISO 8601 із суфіксом 'Z'.

    Args:
        dt: Об'єкт datetime для перетворення або None.

    Returns:
        Рядок у форматі ISO 8601 (наприклад, "2025-10-21T10:00:00Z") або
        None, якщо вхідний об'єкт був None.
    """
    if not dt:
        return None
    if dt.tzinfo is None:
        # Трактуємо naive datetime як UTC
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        # Конвертуємо aware datetime в UTC
        dt = dt.astimezone(timezone.utc)

    # isoformat() для UTC може повернути +00:00, замінюємо на Z для консистентності
    return dt.isoformat().replace('+00:00', 'Z')