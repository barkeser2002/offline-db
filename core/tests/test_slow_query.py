import pytest
import time
import logging
from unittest.mock import patch
from django.db import connection
from core.utils import slow_query_logger

@pytest.fixture
def mock_execute():
    def execute(sql, params, many, context):
        return "result"
    return execute

def test_slow_query_logger_fast_query(mock_execute, caplog):
    # Setup caplog
    caplog.set_level(logging.WARNING)

    # Call with a fast query simulation
    with patch('time.monotonic', side_effect=[0.0, 0.05]):
        result = slow_query_logger(mock_execute, "SELECT 1", [], False, {})

    assert result == "result"
    assert "Slow query detected" not in caplog.text

def test_slow_query_logger_slow_query(mock_execute, caplog):
    # Setup caplog
    caplog.set_level(logging.WARNING)

    # Call with a slow query simulation (> 100ms)
    with patch('time.monotonic', side_effect=[0.0, 0.15]):
        result = slow_query_logger(mock_execute, "SELECT 1", [], False, {})

    assert result == "result"
    assert "Slow query detected" in caplog.text
    assert "SELECT 1" in caplog.text

@pytest.mark.django_db
def test_apps_ready():
    # Verify the execute wrapper is attached to new connections via signal
    from django.db import connection as thread_connection
    # Force connection creation if not already created
    thread_connection.ensure_connection()
    assert slow_query_logger in thread_connection.execute_wrappers
