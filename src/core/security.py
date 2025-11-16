from datetime import datetime, timedelta, timezone
from jose import jwt
from src.core.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES
from typing import Iterable, Optional

def create_access_token(data: dict):
    to_encode = data.copy()
    # Replace API Call / Use timezone-aware datetime
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": int(expire.timestamp())})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

ALLOWED_ROLES: set[str] = {"student", "teacher", "supervisor"}
ROLE_SYNONYMS: dict[str, str] = {
    "student": "student",
    "teacher": "teacher",
    "supervisor": "supervisor",
    "instructor": "teacher",
    "lecturer":  "teacher",
    "professor": "teacher",
    "invigilator": "supervisor",
    "monitor":  "supervisor",
    "proctor": "supervisor",
    "студент":  "student",
    "викладач": "teacher",
    "наглядач": "supervisor",
    "наглядач-супервізор": "supervisor",
}

def _canonical_role(value: Optional[str]) -> Optional[str]:
    """Return canonical role name or None if empty/unknown."""
    if value is None:
        return None
    s = str(value).strip().lower()
    if not s:
        return None
    if s in ROLE_SYNONYMS:
        return ROLE_SYNONYMS[s]
    return s if s in ALLOWED_ROLES else None

def has_roles(
    user_roles: Iterable[str] | None,
    required: Iterable[str] | None,
    *,
    mode: str = "any",
    strict: bool = False
) -> bool:
    """
    Determine whether a user's roles satisfy a requirement.

    Canonical roles: {'student','teacher','supervisor'}.
    English and Ukrainian synonyms are mapped. Unknown roles are ignored by
    default, or raise ValueError when strict=True.
    """

    def _normalize(items: Iterable[str] | None) -> set[str]:
        """Return set of canonical roles, ignoring empty or unknown ones."""
        if not items:
            return set()
        roles = { _canonical_role(r.strip().casefold()) for r in items if r and r.strip() }
        return {r for r in roles if r}

    def _find_unknown(items: Iterable[str] | None) -> list[str]:
        """Return list of roles that cannot be canonicalized."""
        if not items:
            return []
        return [
            r for r in items
            if r and not r.isspace() and not _canonical_role(r)
        ]

    def _normalize_and_validate(items: Iterable[str] | None) -> set[str]:
        roles = _normalize(items)
        if strict:
            unknown = _find_unknown(items)
            if unknown:
                raise ValueError(f"Unknown roles: {', '.join(unknown)}")
        return roles

    user_roles_set = _normalize_and_validate(user_roles)
    required_roles_set = _normalize_and_validate(required)

    if not required_roles_set:
        return True
    if not user_roles_set:
        return False

    if mode == "all":
        return required_roles_set <= user_roles_set
    return bool(user_roles_set & required_roles_set)
