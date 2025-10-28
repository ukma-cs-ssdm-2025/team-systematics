from src.api.repositories.certificate_repository import CertificateRepository
from src.api.schemas.certificate import CertificateResponse, AverageGradeResponse
from fastapi import HTTPException, status

class CertificateService:
    def __init__(self, certificate_repository: CertificateRepository):
        self.certificate_repository = certificate_repository

    def get_certificate(self, user_id: str) -> CertificateResponse:
        certificate_data = self.certificate_repository.get_certificate(user_id)
        if not certificate_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
        return certificate_data

    def get_average_grade(self, user_id: str) -> AverageGradeResponse:
        avg_grade_data = self.certificate_repository.get_average_grade(user_id)
        if not avg_grade_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Average grade not found")
        return avg_grade_data

    def sort_tests(self, column: str, user_id: str) -> CertificateResponse:
        sorted_tests = self.certificate_repository.sort_tests(column, user_id)
        return sorted_tests
