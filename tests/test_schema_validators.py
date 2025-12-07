"""
Tests for Pydantic schema validators and model edge cases.
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from pydantic import ValidationError

from src.api.schemas.exams import (
    ExamCreate, ExamUpdate, datetime_must_not_be_in_past,
    end_at_must_be_after_start_at
)


class TestExamValidators:
    """Tests for Exam schema validators."""
    
    def test_start_at_past_raises_error(self):
        """Test that start_at in the past raises ValidationError."""
        past_time = datetime.now(timezone.utc) - timedelta(days=1)
        
        with pytest.raises(ValidationError) as exc_info:
            ExamCreate(
                title="Past Exam",
                start_at=past_time,
                end_at=past_time + timedelta(hours=2),
                owner_id=uuid4()
            )
        
        assert "минулому" in str(exc_info.value) or "past" in str(exc_info.value).lower()
    
    def test_end_at_past_raises_error(self):
        """Test that end_at in the past raises ValidationError."""
        past_time = datetime.now(timezone.utc) - timedelta(days=1)
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        
        with pytest.raises(ValidationError) as exc_info:
            ExamCreate(
                title="Invalid End Exam",
                start_at=future_time,
                end_at=past_time,
                owner_id=uuid4()
            )
        
        # Should fail either on end_at being in past or on end_at < start_at
        assert len(exc_info.value.errors()) > 0
    
    def test_end_at_before_start_at_raises_error(self):
        """Test that end_at before start_at raises ValidationError."""
        now = datetime.now(timezone.utc)
        start_time = now + timedelta(hours=2)
        end_time = now + timedelta(hours=1)
        
        with pytest.raises(ValidationError) as exc_info:
            ExamCreate(
                title="Invalid Times",
                start_at=start_time,
                end_at=end_time,
                owner_id=uuid4()
            )
        
        assert "after" in str(exc_info.value).lower() or len(exc_info.value.errors()) > 0
    
    def test_end_at_equals_start_at_raises_error(self):
        """Test that end_at equal to start_at raises ValidationError."""
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        
        with pytest.raises(ValidationError) as exc_info:
            ExamCreate(
                title="Same Times",
                start_at=future_time,
                end_at=future_time,
                owner_id=uuid4()
            )
        
        assert "after" in str(exc_info.value).lower()
    
    def test_valid_exam_create(self):
        """Test creating valid ExamCreate schema."""
        now = datetime.now(timezone.utc)
        start_time = now + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        owner_id = uuid4()
        
        exam = ExamCreate(
            title="Valid Exam",
            start_at=start_time,
            end_at=end_time,
            duration_minutes=120,
            max_attempts=3,
            pass_threshold=70,
            owner_id=owner_id
        )
        
        assert exam.title == "Valid Exam"
        assert exam.start_at == start_time
        assert exam.end_at == end_time
        assert exam.max_attempts == 3
    
    def test_exam_create_title_too_short(self):
        """Test that title with < 3 characters raises ValidationError."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        
        with pytest.raises(ValidationError):
            ExamCreate(
                title="AB",
                start_at=future_time,
                end_at=future_time + timedelta(hours=1),
                owner_id=uuid4()
            )
    
    def test_exam_create_title_too_long(self):
        """Test that title with > 100 characters raises ValidationError."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        long_title = "A" * 101
        
        with pytest.raises(ValidationError):
            ExamCreate(
                title=long_title,
                start_at=future_time,
                end_at=future_time + timedelta(hours=1),
                owner_id=uuid4()
            )
    
    def test_exam_create_invalid_max_attempts(self):
        """Test that invalid max_attempts raises ValidationError."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        
        with pytest.raises(ValidationError):
            ExamCreate(
                title="Invalid Attempts",
                start_at=future_time,
                end_at=future_time + timedelta(hours=1),
                max_attempts=11,  # > 10
                owner_id=uuid4()
            )
    
    def test_exam_create_invalid_pass_threshold(self):
        """Test that invalid pass_threshold raises ValidationError."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        
        with pytest.raises(ValidationError):
            ExamCreate(
                title="Invalid Threshold",
                start_at=future_time,
                end_at=future_time + timedelta(hours=1),
                pass_threshold=101,  # > 100
                owner_id=uuid4()
            )
    
    def test_exam_update_with_dates_validation(self):
        """Test ExamUpdate with date validation."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        start_time = future_time + timedelta(hours=2)
        end_time = start_time + timedelta(hours=2)
        
        # Valid update
        exam_update = ExamUpdate(
            title="Updated Exam",
            start_at=start_time,
            end_at=end_time
        )
        
        assert exam_update.title == "Updated Exam"
    
    def test_exam_update_end_before_start_raises_error(self):
        """Test ExamUpdate with end_at before start_at raises error."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        start_time = future_time + timedelta(hours=2)
        end_time = future_time + timedelta(hours=1)
        
        with pytest.raises(ValidationError):
            ExamUpdate(
                start_at=start_time,
                end_at=end_time
            )


class TestDatetimeValidator:
    """Tests for datetime_must_not_be_in_past function."""
    
    def test_datetime_must_not_be_in_past_with_past_date(self):
        """Test validator rejects past datetime."""
        past_time = datetime.now(timezone.utc) - timedelta(days=1)
        
        with pytest.raises(ValueError) as exc_info:
            datetime_must_not_be_in_past(None, past_time)
        
        assert "минулому" in str(exc_info.value) or "past" in str(exc_info.value).lower()
    
    def test_datetime_must_not_be_in_past_with_future_date(self):
        """Test validator accepts future datetime."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        result = datetime_must_not_be_in_past(None, future_time)
        assert result == future_time
    
    def test_datetime_must_not_be_in_past_with_none(self):
        """Test validator accepts None."""
        result = datetime_must_not_be_in_past(None, None)
        assert result is None


class TestEndAtValidator:
    """Tests for end_at_must_be_after_start_at function."""
    
    def test_end_at_after_start_at(self):
        """Test validator accepts end_at after start_at."""
        start = datetime.now(timezone.utc) + timedelta(hours=1)
        end = start + timedelta(hours=2)
        values = {"start_at": start}
        
        result = end_at_must_be_after_start_at(None, end, values)
        assert result == end
    
    def test_end_at_equals_start_at_raises_error(self):
        """Test validator rejects end_at equal to start_at."""
        start = datetime.now(timezone.utc) + timedelta(hours=1)
        values = {"start_at": start}
        
        with pytest.raises(ValueError):
            end_at_must_be_after_start_at(None, start, values)
    
    def test_end_at_before_start_at_raises_error(self):
        """Test validator rejects end_at before start_at."""
        start = datetime.now(timezone.utc) + timedelta(hours=2)
        end = start - timedelta(hours=1)
        values = {"start_at": start}
        
        with pytest.raises(ValueError):
            end_at_must_be_after_start_at(None, end, values)
    
    def test_end_at_with_no_start_at(self):
        """Test validator accepts end_at when start_at not set."""
        end = datetime.now(timezone.utc) + timedelta(hours=1)
        values = {}
        
        result = end_at_must_be_after_start_at(None, end, values)
        assert result == end
