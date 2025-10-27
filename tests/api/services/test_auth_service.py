import pytest
from uuid import uuid4
from fastapi import HTTPException

import src.api.services.auth_service as svc_module
from src.api.services.auth_service import AuthService
from src.api.schemas.auth import LoginRequest


class StubUser:
    """Minimal user object to satisfy AuthService fields."""
    def __init__(self, *, id, email, hashed_password, first_name="", last_name=""):
        self.id = id
        self.email = email
        self.hashed_password = hashed_password
        self.first_name = first_name
        self.last_name = last_name


def make_fake_repo(*, user_to_return=None, roles_to_return=None):
    """Factory that returns a fake repository class with preset behavior."""

    class FakeUserRepository:
        def __init__(self, db):
            self._db = db

        def get_user_by_email(self, email):
            return user_to_return

        def get_user_roles(self, user_id):
            return roles_to_return or []

    return FakeUserRepository


def test_login_user_not_found(monkeypatch):
    """Service should raise 401 when repository returns no user."""
    monkeypatch.setattr(svc_module, "UserRepository", make_fake_repo(user_to_return=None))

    svc = AuthService()
    req = LoginRequest(email="ghost@example.com", password="pw")

    with pytest.raises(HTTPException) as ei:
        svc.login(db=None, request=req)
    assert ei.value.status_code == 401
    assert "User not found" in str(ei.value.detail)


def test_login_invalid_password(monkeypatch):
    """Service should raise 401 when verify_password is False."""
    user = StubUser(
        id=uuid4(),
        email="u@example.com",
        hashed_password="<stored-hash>",
        first_name="Test",
        last_name="User",
    )

    monkeypatch.setattr(svc_module, "UserRepository", make_fake_repo(user_to_return=user))
    monkeypatch.setattr(svc_module, "verify_password", lambda plain, hashed: False)

    svc = AuthService()
    with pytest.raises(HTTPException) as ei:
        svc.login(db=None, request=LoginRequest(email=user.email, password="bad"))
    assert ei.value.status_code == 401
    assert "Invalid password" in str(ei.value.detail)


def test_login_success_with_roles_and_token(monkeypatch):
    """Successful path: password OK, roles fetched, token created, response shape is correct."""
    user_id = uuid4()
    user = StubUser(
        id=user_id,
        email="u@example.com",
        hashed_password="<stored-hash>",
        first_name="Test",
        last_name="User",
    )
    roles = ["student", "admin"]
    monkeypatch.setattr(svc_module, "UserRepository", make_fake_repo(user_to_return=user, roles_to_return=roles))
    monkeypatch.setattr(svc_module, "verify_password", lambda plain, hashed: True)

    captured = {}
    def fake_create_access_token(payload: dict):
        captured.update(payload)
        return "stub-token"

    monkeypatch.setattr(svc_module, "create_access_token", fake_create_access_token)

    svc = AuthService()
    resp = svc.login(db=None, request=LoginRequest(email=user.email, password="good"))

    assert resp.token_type == "bearer"
    assert resp.access_token == "stub-token"
    assert resp.user.email == "u@example.com"
    assert resp.user.roles == roles
    assert resp.user.full_name == "Test User"

    assert captured.get("sub") == str(user_id)
    assert captured.get("roles") == roles


def test_login_full_name_trims_spaces_when_last_name_missing(monkeypatch):
    """If last_name is empty, full_name should not have trailing spaces after strip()."""
    user_id = uuid4()
    user = StubUser(
        id=user_id,
        email="solo@example.com",
        hashed_password="<stored-hash>",
        first_name="Solo",
        last_name="",
    )

    monkeypatch.setattr(svc_module, "UserRepository", make_fake_repo(user_to_return=user, roles_to_return=[]))
    monkeypatch.setattr(svc_module, "verify_password", lambda p, h: True)
    monkeypatch.setattr(svc_module, "create_access_token", lambda payload: "stub-token")

    svc = AuthService()
    resp = svc.login(db=None, request=LoginRequest(email=user.email, password="ok"))

    assert resp.user.full_name == "Solo"
    assert resp.user.roles == []
