from pydantic import BaseModel
from typing import List, Optional

class CertificateTest(BaseModel):
    name: str
    course: str
    status: str
    attempts: int
    due_date: str
    score: float
    time: str

class CertificateResponse(BaseModel):
    tests: List[CertificateTest]

class AverageGradeResponse(BaseModel):
    course: str
    average_score: float
