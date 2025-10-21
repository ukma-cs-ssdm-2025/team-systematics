import pytest
from src.core.security import has_roles

def test_case_insensitive_and_trim_whitespace():
    """Comparison should ignore case and surrounding spaces."""
    user_roles = [" Student ", "AdMiN"]
    assert has_roles(user_roles, ["student"]) is True
    assert has_roles(user_roles, ["admin"], mode="all") is True
    assert has_roles(user_roles, ["student", "admin"], mode="all") is True

def test_english_synonyms_are_mapped_to_canonical():
    """'instructor' -> teacher; 'invigilator' -> proctor."""
    assert has_roles(["instructor"], ["teacher"]) is True
    assert has_roles(["invigilator"], ["proctor"]) is True

def test_ukrainian_synonyms_supported():
    """Ukrainian synonyms map to canonical roles."""
    assert has_roles(["викладач"], ["teacher"]) is True
    assert has_roles(["наглядач"], ["proctor"]) is True
    assert has_roles(["студент"], ["student"]) is True

def test_unknown_roles_ignored_by_default():
    """Unknown roles are ignored when strict=False (default)."""
    assert has_roles(["unknown_role", "student"], ["student"]) is True
    assert has_roles(["unknown_role"], ["student"]) is False

def test_strict_mode_raises_on_unknown():
    with pytest.raises(ValueError):
        has_roles(["student", "mystery"], ["student"], strict=True)

def test_generators_are_supported():
    user_iter = (r for r in ["student", "admin"])
    req_iter = (r for r in ["admin"])
    assert has_roles(user_iter, req_iter) is True
