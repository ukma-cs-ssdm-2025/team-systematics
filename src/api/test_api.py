import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.main import app

client = TestClient(app)

def create_exam_payload(title="Test Exam", description="Some instructions"):
    """Генерує payload для створення екзамену відповідно до ExamCreate"""
    now = datetime.utcnow()
    return {
        "title": title,
        "instructions": description,
        "start_at": (now - timedelta(days=1)).isoformat(),
        "end_at": (now + timedelta(days=1)).isoformat(),
        "max_attempts": 3,
        "pass_threshold": 60,
        "owner_id": str(uuid4()),
    }


def test_list_exams():
    response = client.get("/api/exams")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_create_exam():
    payload = create_exam_payload(title="Python Fundamentals", description="Test exam for beginners")
    response = client.post("/api/exams", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert "id" in data


def test_get_exam_by_id():
    payload = create_exam_payload(title="Temporary Exam")
    create_res = client.post("/api/exams", json=payload)
    exam_id = create_res.json()["id"]

    response = client.get(f"/api/exams/{exam_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == exam_id


def test_start_attempt():
    exam_payload = create_exam_payload(title="Exam for attempt")
    exam_res = client.post("/api/exams", json=exam_payload)
    exam_id = exam_res.json()["id"]

    attempt_payload = {"user_id": str(uuid4())}
    response = client.post(f"/api/exams/{exam_id}/attempts", json=attempt_payload)
    assert response.status_code == 201

    attempt = response.json()
    print("DEBUG test_start_attempt -> Exam ID:", exam_id)
    print("DEBUG test_start_attempt -> Attempt ID:", attempt["id"])

    assert attempt["status"] == "in_progress"
    assert attempt["exam_id"] == exam_id


def test_add_answer_and_submit():
    exam_payload = create_exam_payload(title="Exam with answer")
    exam_res = client.post("/api/exams", json=exam_payload)
    exam_id = exam_res.json()["id"]

    attempt_payload = {"user_id": str(uuid4())}
    attempt_res = client.post(f"/api/exams/{exam_id}/attempts", json=attempt_payload)
    assert attempt_res.status_code == 201

    attempt = attempt_res.json()
    attempt_id = attempt["id"]
    print("DEBUG test_add_answer_and_submit -> Exam ID:", exam_id)
    print("DEBUG test_add_answer_and_submit -> Attempt ID:", attempt_id)

    answer_payload = {
        "question_id": str(uuid4()),
        "answer": "Test answer"
    }
    ans_res = client.post(f"/api/attempts/{attempt_id}/answers", json=answer_payload)
    assert ans_res.status_code == 201

    submit_res = client.post(f"/api/attempts/{attempt_id}/submit")
    assert submit_res.status_code == 201
