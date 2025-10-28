from fastapi import APIRouter, Depends, HTTPException, status
from src.api.services.certificate_service import CertificateService
from src.api.schemas.certificate import CertificateResponse, AverageGradeResponse
from src.api.repositories.certificate_repository import CertificateRepository
from src.api.dependencies import get_current_user

router = APIRouter()

class CertificateController:
    def __init__(self, certificate_service: CertificateService):
        self.certificate_service = certificate_service

    @router.get("/certificate", response_model=CertificateResponse)
    def get_certificate(self, current_user: str = Depends(get_current_user)):
        # Перевірка прав доступу
        if current_user != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")
        
        # Отримання даних для атестату
        certificate_data = self.certificate_service.get_certificate(current_user)
        return certificate_data

    @router.get("/certificate/average-grade", response_model=AverageGradeResponse)
    def get_average_grade(self, current_user: str = Depends(get_current_user)):
        # Статистика середнього балу
        avg_grade_data = self.certificate_service.get_average_grade(current_user)
        return avg_grade_data

    @router.get("/certificate/sort", response_model=CertificateResponse)
    def sort_tests(self, column: str, current_user: str = Depends(get_current_user)):
        # Сортування тестів за колонкою
        sorted_tests = self.certificate_service.sort_tests(column, current_user)
        return sorted_tests
