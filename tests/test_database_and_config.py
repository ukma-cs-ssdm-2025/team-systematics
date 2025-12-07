"""
Tests for database configuration and utilities.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from src.api.database import get_json_type, get_db
from src.core.config import DATABASE_URL, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB


class TestDatabaseUtilities:
    """Tests for database utility functions."""
    
    def test_get_json_type_postgresql(self):
        """Test get_json_type returns JSONB for PostgreSQL."""
        with patch('src.api.database.DATABASE_URL', 'postgresql://user:pass@localhost/db'):
            from src.api.database import get_json_type as get_json_type_patched
            # We need to import after patching, so we use the global function
            result = get_json_type()
            # Result should be JSONB for PostgreSQL
            assert result == JSONB
    
    def test_get_json_type_sqlite(self):
        """Test get_json_type returns JSON for SQLite."""
        with patch('src.api.database.DATABASE_URL', 'sqlite:///:memory:'):
            result = get_json_type()
            # Result should be JSON for SQLite
            assert result == JSON
    
    def test_get_json_type_no_database_url(self):
        """Test get_json_type returns JSON when DATABASE_URL is None."""
        with patch('src.api.database.DATABASE_URL', None):
            result = get_json_type()
            assert result == JSON


class TestConfigValues:
    """Tests for configuration values."""
    
    def test_database_url_exists(self):
        """Test DATABASE_URL is configured."""
        assert DATABASE_URL is not None
        assert isinstance(DATABASE_URL, str)
        assert len(DATABASE_URL) > 0
    
    def test_jwt_secret_exists(self):
        """Test JWT_SECRET is configured."""
        assert JWT_SECRET is not None
        assert isinstance(JWT_SECRET, str)
        assert len(JWT_SECRET) > 0
    
    def test_jwt_algorithm_exists(self):
        """Test JWT_ALGORITHM is configured."""
        assert JWT_ALGORITHM is not None
        assert isinstance(JWT_ALGORITHM, str)
        assert JWT_ALGORITHM == "HS256"
    
    def test_jwt_expiration_minutes(self):
        """Test JWT_EXPIRATION_MINUTES is a positive integer."""
        assert JWT_EXPIRATION_MINUTES is not None
        assert isinstance(JWT_EXPIRATION_MINUTES, int)
        assert JWT_EXPIRATION_MINUTES > 0
