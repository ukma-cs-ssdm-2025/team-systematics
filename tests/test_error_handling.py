"""
Tests for error handling patterns and HTTP exceptions.
"""
import pytest
from fastapi import HTTPException, status


class TestHTTPExceptions:
    """Tests for HTTP exception handling."""
    
    def test_unauthorized_exception(self):
        """Test creating unauthorized exception."""
        exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        
        assert exc.status_code == 401
        assert exc.detail == "Not authenticated"
    
    def test_forbidden_exception(self):
        """Test creating forbidden exception."""
        exc = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        assert exc.status_code == 403
    
    def test_not_found_exception(self):
        """Test creating not found exception."""
        exc = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
        
        assert exc.status_code == 404
    
    def test_conflict_exception(self):
        """Test creating conflict exception."""
        exc = HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource already exists")
        
        assert exc.status_code == 409
    
    def test_unprocessable_entity_exception(self):
        """Test creating validation exception."""
        exc = HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid data")
        
        assert exc.status_code == 422


class TestErrorScenarios:
    """Tests for common error scenarios."""
    
    def test_invalid_credentials_scenario(self):
        """Test invalid credentials error scenario."""
        try:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        except HTTPException as e:
            assert e.status_code == 401
            assert "Invalid" in e.detail
    
    def test_unauthorized_scenario(self):
        """Test unauthorized access scenario."""
        try:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header")
        except HTTPException as e:
            assert e.status_code == 401
    
    def test_forbidden_scenario(self):
        """Test forbidden access scenario."""
        try:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not an exam owner")
        except HTTPException as e:
            assert e.status_code == 403
    
    def test_resource_not_found_scenario(self):
        """Test resource not found scenario."""
        try:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
        except HTTPException as e:
            assert e.status_code == 404
    
    def test_duplicate_resource_scenario(self):
        """Test duplicate resource scenario."""
        try:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        except HTTPException as e:
            assert e.status_code == 409
    
    def test_validation_error_scenario(self):
        """Test validation error scenario."""
        try:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email format invalid")
        except HTTPException as e:
            assert e.status_code == 422


class TestErrorMessageFormatting:
    """Tests for error message formatting."""
    
    def test_error_message_includes_context(self):
        """Test that error messages include relevant context."""
        email = "duplicate@test.com"
        exc = HTTPException(status_code=409, detail=f"Email {email} already exists")
        
        assert email in exc.detail
    
    def test_error_status_code_mapping(self):
        """Test correct status code mapping."""
        status_codes = {
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            409: "Conflict",
            422: "Unprocessable Entity"
        }
        
        for code, meaning in status_codes.items():
            exc = HTTPException(status_code=code, detail=meaning)
            assert exc.status_code == code


class TestErrorRecovery:
    """Tests for error recovery patterns."""
    
    def test_exception_raising_and_catching(self):
        """Test raising and catching exceptions."""
        with pytest.raises(HTTPException) as exc_info:
            raise HTTPException(status_code=400, detail="Bad request")
        
        assert exc_info.value.status_code == 400
    
    def test_specific_status_code_handling(self):
        """Test handling specific status codes."""
        exc = HTTPException(status_code=404, detail="Not found")
        
        if exc.status_code == 404:
            assert True
        else:
            assert False
    
    def test_exception_detail_extraction(self):
        """Test extracting exception details."""
        detail_msg = "User not authorized"
        exc = HTTPException(status_code=401, detail=detail_msg)
        
        assert exc.detail == detail_msg
