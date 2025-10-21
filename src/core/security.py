from datetime import datetime, timedelta
from jose import jwt
from src.core.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES
from typing import Iterable, Optional

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

ALLOWED_ROLES: set[str] = {"student", "teacher", "proctor"}
ROLE_SYNONYMS: dict[str, str] = {
    "student": "student",
    "teacher": "teacher",
    "proctor": "proctor",
    "instructor": "teacher",
    "lecturer":  "teacher",
    "professor": "teacher",
    "invigilator": "proctor",
    "monitor":  "proctor",
    "студент":  "student",
    "викладач": "teacher",
    "наглядач": "proctor",
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

def has_roles(user_roles: Iterable[str] | None,
              required: Iterable[str] | None,
              *, mode: str = "any",
              strict: bool = False) -> bool:
    """
    Check roles with canonicalization.
    Unknown roles are ignored.
    """
    def _norm(items: Iterable[str] | None) -> set[str]:
        unknown: list[str] = []
        out: set[str] = set()
        for x in (items or []):
            canon = _canonical_role(x)
            if canon:
                out.add(canon)
            else:
                if x not in (None, "", " "):
                    unknown.append(str(x))
        if strict and unknown:
            raise ValueError(f"Unknown roles: {', '.join(unknown)}")
        return out

    ur = _norm(user_roles)
    req = _norm(required)

    if not req:
        return True
    if not ur:
        return False

    if mode == "all":
        return req.issubset(ur)
    return bool(ur & req)
