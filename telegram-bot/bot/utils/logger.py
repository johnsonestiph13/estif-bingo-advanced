# utils/logger.py
"""Structured logging utilities for the bot"""

import logging
import sys
import json
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps
from ..config import LOG_LEVEL, LOG_FORMAT

# ==================== LOGGER SETUP ====================

def setup_logger(name: str = "estif_bingo") -> logging.Logger:
    """Setup and return configured logger"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    return logger

# Default logger instance
logger = setup_logger()

# ==================== STRUCTURED LOGGING ====================

def log_event(event: str, level: str = "info", **kwargs) -> None:
    """Log structured event with additional data"""
    log_data = {
        "event": event,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }
    
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(json.dumps(log_data))

def log_user_action(telegram_id: int, action: str, status: str, **kwargs) -> None:
    """Log user-specific actions"""
    log_event(
        "user_action",
        level="info",
        telegram_id=telegram_id,
        action=action,
        status=status,
        **kwargs
    )

def log_error(error: Exception, context: Optional[Dict] = None) -> None:
    """Log error with full context"""
    log_event(
        "error",
        level="error",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {}
    )

def log_api_call(endpoint: str, method: str, status_code: int, duration_ms: float) -> None:
    """Log API call metrics"""
    log_event(
        "api_call",
        level="info",
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        duration_ms=round(duration_ms, 2)
    )

def log_database_query(query_name: str, duration_ms: float, row_count: int = None) -> None:
    """Log database query performance"""
    log_data = {
        "query": query_name,
        "duration_ms": round(duration_ms, 2)
    }
    if row_count is not None:
        log_data["row_count"] = row_count
    
    log_event("database_query", level="debug", **log_data)

# ==================== DECORATORS ====================

def log_function_call(func):
    """Decorator to log function calls with arguments"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Completed {func.__name__}")
            return result
        except Exception as e:
            log_error(e, {"function": func.__name__})
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Completed {func.__name__}")
            return result
        except Exception as e:
            log_error(e, {"function": func.__name__})
            raise
    
    # Check if function is async
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

def log_performance(func):
    """Decorator to log function execution time"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        import time
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = (time.time() - start) * 1000
            logger.debug(f"{func.__name__} took {duration:.2f}ms")
            return result
        except Exception as e:
            duration = (time.time() - start) * 1000
            logger.error(f"{func.__name__} failed after {duration:.2f}ms: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        import time
        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration = (time.time() - start) * 1000
            logger.debug(f"{func.__name__} took {duration:.2f}ms")
            return result
        except Exception as e:
            duration = (time.time() - start) * 1000
            logger.error(f"{func.__name__} failed after {duration:.2f}ms: {e}")
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

# ==================== CONTEXT MANAGERS ====================

class RequestLogger:
    """Context manager for logging request processing"""
    
    def __init__(self, request_name: str):
        self.request_name = request_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        logger.info(f"Starting {self.request_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds() * 1000
        if exc_type:
            logger.error(f"{self.request_name} failed after {duration:.2f}ms: {exc_val}")
        else:
            logger.info(f"{self.request_name} completed in {duration:.2f}ms")

# ==================== EXPORTS ====================

__all__ = [
    'logger',
    'setup_logger',
    'log_event',
    'log_user_action',
    'log_error',
    'log_api_call',
    'log_database_query',
    'log_function_call',
    'log_performance',
    'RequestLogger'
]