"""
Tests for hashing utility functions.
"""
import pytest
from unittest.mock import patch
from src.utils.hashing import get_password_hash, verify_password, truncate_utf8


class TestTruncateUtf8:
    """Tests for truncate_utf8 function."""
    
    def test_truncate_string_within_limit(self):
        """Test truncate_utf8 with string within limit."""
        result = truncate_utf8("hello", 72)
        assert result == "hello"
    
    def test_truncate_string_exceeding_limit(self):
        """Test truncate_utf8 with string exceeding byte limit."""
        long_string = "a" * 100
        result = truncate_utf8(long_string, 10)
        assert len(result.encode('utf-8')) <= 10
    
    def test_truncate_unicode_string(self):
        """Test truncate_utf8 with unicode characters."""
        unicode_string = "привіт" * 20  # Cyrillic characters
        result = truncate_utf8(unicode_string, 72)
        assert len(result.encode('utf-8')) <= 72


def test_hash_password():
    """Test password hashing."""
    password = "secure_password_123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert len(hashed) > 0


def test_verify_password_correct():
    """Test verification with correct password."""
    password = "secure_password_123"
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    """Test verification with incorrect password."""
    password = "secure_password_123"
    wrong_password = "wrong_password_456"
    hashed = get_password_hash(password)
    
    assert verify_password(wrong_password, hashed) is False


def test_verify_password_empty_string():
    """Test verification with empty password."""
    hashed = get_password_hash("test")
    
    assert verify_password("", hashed) is False


def test_hash_consistency_different_inputs():
    """Test that different passwords produce different hashes."""
    password1 = "password_one"
    password2 = "password_two"
    
    hashed1 = get_password_hash(password1)
    hashed2 = get_password_hash(password2)
    
    assert hashed1 != hashed2


def test_verify_password_with_bytes_hash():
    """Test verify_password with hash as bytes."""
    password = "testpass"
    hashed = get_password_hash(password)
    hashed_bytes = hashed.encode('utf-8')
    result = verify_password(password, hashed_bytes)
    assert result is True


def test_verify_unicode_password():
    """Test verify_password with unicode characters."""
    password = "пароль123"
    hashed = get_password_hash(password)
    result = verify_password(password, hashed)
    assert result is True


def test_verify_long_password_truncation():
    """Test verify_password handles truncation of long passwords."""
    long_password = "a" * 100
    hashed = get_password_hash(long_password)
    result = verify_password(long_password, hashed)
    assert result is True


@patch('src.utils.hashing.bcrypt.checkpw')
def test_verify_password_with_type_error(mock_checkpw):
    """Test verify_password handles TypeError from bcrypt."""
    mock_checkpw.side_effect = TypeError("Invalid type")
    result = verify_password("password", "hash")
    assert result is False


@patch('src.utils.hashing.bcrypt.checkpw')
def test_verify_password_with_value_error(mock_checkpw):
    """Test verify_password handles ValueError from bcrypt."""
    mock_checkpw.side_effect = ValueError("Invalid hash")
    result = verify_password("password", "hash")
    assert result is False


@patch('src.utils.hashing.bcrypt.checkpw')
def test_verify_password_with_generic_exception(mock_checkpw):
    """Test verify_password handles generic exceptions from bcrypt."""
    mock_checkpw.side_effect = Exception("Unknown error")
    result = verify_password("password", "hash")
    assert result is False
