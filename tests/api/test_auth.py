import pytest
from types import SimpleNamespace
from uuid import uuid4
from fastapi import HTTPException

from src.api.services.auth_service import AuthService


# -----------------------------
# Dummy models (lightweight versions)
# -----------------------------
class DummyUser:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid4())
        self.email = kwargs.get("email", "u@example.com")
        self.hashed_password = kwargs.get("hashed_password", "hashed_pwd")
        self.first_name = kwargs.get("first_name", "FN")
        self.last_name = kwargs.get("last_name", "LN")
        self.patronymic = kwargs.get("patronymic", None)
        self.avatar_url = kwargs.get("avatar_url", None)


class DummyRole:
    name = "student"

    def __init__(self, id=1, name="student"):
        self.id = id
        self.name = name


class DummyUserRole:
    def __init__(self, user_id, role_id):
        self.user_id = user_id
        self.role_id = role_id


class DummyMajor:
    id = 1

    def __init__(self, id=1, name="IT"):
        self.id = id
        self.name = name



class DummyUserMajor:
    def __init__(self, user_id, major_id):
        self.user_id = user_id
        self.major_id = major_id


# -----------------------------
# Fake DB session
# -----------------------------
class FakeQuery:
    def __init__(self, result=None):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class FakeDB:
    def __init__(self, roles=None, majors=None):
        self.roles = roles or {}
        self.majors = majors or {}
        self.added = []
        self.committed = False
        self.flushed = False
        self.refreshed = []

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.flushed = True

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        self.refreshed.append(obj)

    def query(self, model):
        import src.api.services.auth_service as M
        if model is M.Role:
            return FakeQuery(self.roles.get("student"))
        if model is M.Major:
            return FakeQuery(self.majors.get("major"))
        return FakeQuery()


# -----------------------------
# Tests for login()
# -----------------------------
def test_login_user_not_found(monkeypatch):
    class FakeRepo:
        def __init__(self, db):
            pass

        def get_user_by_email(self, email):
            return None

    monkeypatch.setattr("src.api.services.auth_service.UserRepository", FakeRepo)

    service = AuthService()
    req = SimpleNamespace(email="missing@ex.com", password="x")

    with pytest.raises(HTTPException) as e:
        service.login(db=object(), request=req)

    assert e.value.status_code == 401
    assert "User not found" in e.value.detail


def test_login_invalid_password(monkeypatch):
    dummy = DummyUser()

    class FakeRepo:
        def __init__(self, db):
            pass

        def get_user_by_email(self, email):
            return dummy

    monkeypatch.setattr("src.api.services.auth_service.UserRepository", FakeRepo)
    monkeypatch.setattr("src.api.services.auth_service.verify_password", lambda p, hp: False)

    service = AuthService()
    req = SimpleNamespace(email=dummy.email, password="wrong")

    with pytest.raises(HTTPException) as e:
        service.login(db=object(), request=req)

    assert e.value.status_code == 401
    assert "Invalid password" in e.value.detail


def test_login_success(monkeypatch):
    dummy = DummyUser()

    class FakeRepo:
        def __init__(self, db):
            pass

        def get_user_by_email(self, email):
            return dummy

        def get_user_roles(self, user_id):
            return ["student", "teacher"]

        def get_user_major(self, user_id):
            return "Economics"

    created_payload = {}

    def fake_token(payload):
        created_payload.update(payload)
        return "TOKEN123"

    monkeypatch.setattr("src.api.services.auth_service.UserRepository", FakeRepo)
    monkeypatch.setattr("src.api.services.auth_service.verify_password", lambda p, hp: True)
    monkeypatch.setattr("src.api.services.auth_service.create_access_token", fake_token)

    service = AuthService()
    req = SimpleNamespace(email=dummy.email, password="pwd")
    resp = service.login(db=object(), request=req)

    assert resp.access_token == "TOKEN123"
    assert resp.user.email == dummy.email
    assert resp.user.roles == ["student", "teacher"]
    assert resp.user.user_major == "Economics"
    assert created_payload["sub"] == str(dummy.id)


# -----------------------------
# Tests for register()
# -----------------------------
def test_register_user_exists(monkeypatch):
    class FakeRepo:
        def __init__(self, db):
            pass

        def get_user_by_email(self, email):
            return DummyUser()

    monkeypatch.setattr("src.api.services.auth_service.UserRepository", FakeRepo)

    service = AuthService()
    req = SimpleNamespace(
        email="exists@ex.com",
        password="pwd",
        first_name="F",
        last_name="L",
        patronymic=None,
        major_id=None,
    )

    with pytest.raises(HTTPException) as e:
        service.register(db=FakeDB(), request=req)

    assert e.value.status_code == 400


def test_register_student_role_missing(monkeypatch):
    class FakeRepo:
        def __init__(self, db):
            pass

        def get_user_by_email(self, email):
            return None

    db = FakeDB(roles={"student": None})

    monkeypatch.setattr("src.api.services.auth_service.UserRepository", FakeRepo)
    monkeypatch.setattr("src.api.services.auth_service.get_password_hash", lambda p: "HASHED")
    monkeypatch.setattr("src.api.services.auth_service.User", DummyUser)

    service = AuthService()
    req = SimpleNamespace(
        email="no-role@ex.com",
        password="pwd",
        first_name="F",
        last_name="L",
        patronymic=None,
        major_id=None,
    )

    with pytest.raises(HTTPException) as e:
        service.register(db=db, request=req)

    assert e.value.status_code == 500
    assert "student" in e.value.detail


def test_register_success_without_major(monkeypatch):
    # Repo mocks
    class FakeRepo:
        def __init__(self, db):
            pass

        def get_user_by_email(self, email):
            return None

        def get_user_roles(self, user_id):
            return ["student"]

        def get_user_major(self, user_id):
            return None

    token_payload = {}

    def fake_token(payload):
        token_payload.update(payload)
        return "TOK123"

    # Patching internal names
    import src.api.services.auth_service as M
    monkeypatch.setattr(M, "UserRepository", FakeRepo)
    monkeypatch.setattr(M, "get_password_hash", lambda p: "HASH")
    monkeypatch.setattr(M, "create_access_token", fake_token)
    monkeypatch.setattr(M, "User", DummyUser)
    monkeypatch.setattr(M, "Role", DummyRole)
    monkeypatch.setattr(M, "UserRole", DummyUserRole)
    monkeypatch.setattr(M, "Major", DummyMajor)
    monkeypatch.setattr(M, "UserMajor", DummyUserMajor)

    db = FakeDB(roles={"student": DummyRole()})

    req = SimpleNamespace(
        email="new@ex.com",
        password="pwd",
        first_name="F",
        last_name="L",
        patronymic=None,
        major_id=None,
    )

    service = AuthService()
    resp = service.register(db=db, request=req)

    assert resp.access_token == "TOK123"
    assert resp.user.email == "new@ex.com"
    assert resp.user.roles == ["student"]
    assert db.committed
    assert token_payload["sub"]


def test_register_success_with_major(monkeypatch):
    class FakeRepo:
        def __init__(self, db):
            pass

        def get_user_by_email(self, email):
            return None

        def get_user_roles(self, uid):
            return ["student"]

        def get_user_major(self, uid):
            return "IT"

    import src.api.services.auth_service as M
    monkeypatch.setattr(M, "UserRepository", FakeRepo)
    monkeypatch.setattr(M, "get_password_hash", lambda p: "HASH")
    monkeypatch.setattr(M, "User", DummyUser)
    monkeypatch.setattr(M, "Role", DummyRole)
    monkeypatch.setattr(M, "Major", DummyMajor)
    monkeypatch.setattr(M, "UserRole", DummyUserRole)
    monkeypatch.setattr(M, "UserMajor", DummyUserMajor)
    monkeypatch.setattr(M, "create_access_token", lambda payload: "TKN")

    db = FakeDB(
        roles={"student": DummyRole()},
        majors={"major": DummyMajor()},
    )

    req = SimpleNamespace(
        email="maj@ex.com",
        password="pwd",
        first_name="FN",
        last_name="LN",
        patronymic=None,
        major_id=1,
    )

    service = AuthService()
    resp = service.register(db=db, request=req)

    assert resp.access_token == "TKN"
    assert resp.user.user_major == "IT"
    assert db.committed


def test_register_major_not_found_no_error(monkeypatch):
    class FakeRepo:
        def __init__(self, db):
            pass

        def get_user_by_email(self, email):
            return None

        def get_user_roles(self, uid):
            return ["student"]

        def get_user_major(self, uid):
            return None

    import src.api.services.auth_service as M
    monkeypatch.setattr(M, "UserRepository", FakeRepo)
    monkeypatch.setattr(M, "get_password_hash", lambda p: "HASH")
    monkeypatch.setattr(M, "User", DummyUser)
    monkeypatch.setattr(M, "Role", DummyRole)
    monkeypatch.setattr(M, "Major", DummyMajor)   # but DB has no major
    monkeypatch.setattr(M, "UserRole", DummyUserRole)
    monkeypatch.setattr(M, "UserMajor", DummyUserMajor)
    monkeypatch.setattr(M, "create_access_token", lambda payload: "ZZZ")

    db = FakeDB(
        roles={"student": DummyRole()},
        majors={},  # major not found
    )

    req = SimpleNamespace(
        email="x@ex.com",
        password="pwd",
        first_name="X",
        last_name="Y",
        patronymic=None,
        major_id=999,
    )

    service = AuthService()
    resp = service.register(db=db, request=req)

    assert resp.access_token == "ZZZ"
    assert resp.user.email == "x@ex.com"
    assert db.committed
