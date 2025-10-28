from sqlalchemy import func
from src.api.database import Session
from src.models import Test, Certificate
from sqlalchemy.orm import Session as SQLSession

class CertificateRepository:
    def __init__(self, db: SQLSession):
        self.db = db

    def get_certificate(self, user_id: str):
        return self.db.query(Certificate).filter(Certificate.user_id == user_id).all()

    def get_average_grade(self, user_id: str):
        return self.db.query(Test.course, func.avg(Test.score)).filter(Test.user_id == user_id).group_by(Test.course).all()

    def sort_tests(self, column: str, user_id: str):
        return self.db.query(Test).filter(Test.user_id == user_id).order_by(getattr(Test, column)).all()
