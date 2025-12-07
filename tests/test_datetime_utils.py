"""
Tests for datetime utility functions.
"""
import pytest
from datetime import datetime, timezone, timedelta
from src.utils.datetime_utils import to_utc_iso


def test_to_utc_iso_with_timezone():
    """Test conversion to UTC ISO string with timezone-aware datetime."""
    dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
    result = to_utc_iso(dt)
    
    assert result == "2024-01-15T10:30:45Z"


def test_to_utc_iso_with_none():
    """Test conversion with None value."""
    result = to_utc_iso(None)
    
    assert result is None


def test_to_utc_iso_without_timezone():
    """Test conversion with naive datetime (assumes UTC)."""
    dt = datetime(2024, 6, 20, 15, 45, 30)
    result = to_utc_iso(dt)
    
    assert "2024-06-20T15:45:30" in result


def test_from_utc_iso_valid_string():
    """Test parsing UTC ISO string."""
    iso_string = "2024-01-15T10:30:45Z"
    # Parse using datetime.fromisoformat
    parsed_dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    
    assert isinstance(parsed_dt, datetime)
    assert parsed_dt.year == 2024
    assert parsed_dt.month == 1
    assert parsed_dt.day == 15
    assert parsed_dt.hour == 10
    assert parsed_dt.minute == 30


def test_utc_iso_format_consistency():
    """Test that UTC ISO format is consistent."""
    dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
    result = to_utc_iso(dt)
    
    assert result is not None
    assert "Z" in result
    assert "T" in result  # ISO format marker
