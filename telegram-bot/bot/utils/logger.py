# telegram-bot/bot/utils/logger.py
# Estif Bingo 24/7 - Complete Structured Logging Utilities
# Includes: Multi-level logging, JSON logging, Performance tracking, Color output

import logging
import sys
import json
import asyncio
import time
import os
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List, Union
from functools import wraps
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from dataclasses import dataclass, field, asdict
from enum import Enum

from bot.config import LOG_LEVEL, LOG_FORMAT, NODE_ENV

# ==================== CONSTANTS ====================
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5
LOG_RETENTION_DAYS = 30

# ==================== LOG LEVEL ENUM ====================
class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

# ==================== COLOR HANDLER (Development Only) ====================
class ColoredFormatter(logging.Formatter):
    """Custom formatter with color codes for development"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[92m',       # Green
        'WARNING': '\033[93m',    # Yellow
        'ERROR': '\033[91m',      # Red
        'CRITICAL': '\033[95m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        return f"{color}{log_message}{self.COLORS['RESET']}"

# ==================== JSON FORMATTER (Production) ====================
class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging in production"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_entry['extra'] = record.extra_data
        
        return json.dumps(log_entry)

# ==================== LOGGER SETUP ====================
def setup_logger(name: str = "estif_bingo") -> logging.Logger:
    """Setup and return configured logger with multiple handlers"""
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Set level
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Console handler (with color in development)
    console_handler = logging.StreamHandler(sys.stdout)
    if NODE_ENV == 'production':
        console_formatter = logging.Formatter(LOG_FORMAT)
    else:
        console_formatter = ColoredFormatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (rotating by size)
    file_handler = RotatingFileHandler(
        LOG_DIR / "bingo.log",
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT
    )
    file_formatter = JSONFormatter() if NODE_ENV == 'production' else logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Error file handler (only errors)
    error_handler = RotatingFileHandler(
        LOG_DIR / "errors.log",
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    # Daily rotation handler
    daily_handler = TimedRotatingFileHandler(
        LOG_DIR / "daily.log",
        when="midnight",
        interval=1,
        backupCount=LOG_RETENTION_DAYS
    )
    daily_handler.setFormatter(file_formatter)
    logger.addHandler(daily_handler)
    
    return logger

# Default logger instance
logger = setup_logger()

# ==================== LOG LEVEL MANAGER ====================
class LogLevelManager:
    """Dynamic log level manager"""
    
    _instance = None
    _levels: Dict[str, int] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def set_level(self, logger_name: str, level: Union[str, int]):
        """Set log level for specific logger"""
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        
        log_obj = logging.getLogger(logger_name)
        log_obj.setLevel(level)
        self._levels[logger_name] = level
        logger.info(f"Set log level for {logger_name} to {logging.getLevelName(level)}")
    
    def get_level(self, logger_name: str) -> int:
        """Get current log level for logger"""
        return self._levels.get(logger_name, logging.getLogger(logger_name).level)
    
    def get_all_levels(self) -> Dict[str, str]:
        """Get all logger levels"""
        return {name: logging.getLevelName(level) for name, level in self._levels.items()}

# ==================== STRUCTURED LOGGING ====================
@dataclass
class LogEvent:
    """Structured log event"""
    event: str
    level: str = "info"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            "event": self.event,
            "level": self.level,
            "timestamp": self.timestamp.isoformat(),
            **self.extra
        }
        return data
    
    def log(self):
        """Log this event"""
        log_method = getattr(logger, self.level.lower(), logger.info)
        log_method(json.dumps(self.to_dict()))


def log_event(event: str, level: str = "info", **kwargs) -> None:
    """Log structured event with additional data"""
    log_event_obj = LogEvent(event=event, level=level, extra=kwargs)
    log_event_obj.log()


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


def log_error(error: Exception, context: Optional[Dict] = None, log_traceback: bool = True) -> None:
    """Log error with full context and traceback"""
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {}
    }
    
    if log_traceback:
        error_data["traceback"] = traceback.format_exc()
    
    log_event("error", level="error", **error_data)


def log_api_call(endpoint: str, method: str, status_code: int, duration_ms: float, 
                 user_id: Optional[int] = None) -> None:
    """Log API call metrics"""
    log_event(
        "api_call",
        level="info",
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        duration_ms=round(duration_ms, 2),
        user_id=user_id
    )


def log_database_query(query_name: str, duration_ms: float, row_count: int = None, 
                       error: Optional[str] = None) -> None:
    """Log database query performance"""
    data = {
        "query": query_name,
        "duration_ms": round(duration_ms, 2)
    }
    if row_count is not None:
        data["row_count"] = row_count
    if error:
        data["error"] = error
    
    level = "error" if error else "debug"
    log_event("database_query", level=level, **data)


def log_bot_command(user_id: int, command: str, args: List[str], success: bool, 
                    duration_ms: float) -> None:
    """Log bot command execution"""
    log_event(
        "bot_command",
        level="info",
        user_id=user_id,
        command=command,
        args=args,
        success=success,
        duration_ms=round(duration_ms, 2)
    )


def log_game_event(user_id: int, event: str, game_data: Dict[str, Any]) -> None:
    """Log game-related events"""
    log_event(
        "game_event",
        level="info",
        user_id=user_id,
        game_event=event,
        **game_data
    )


def log_transfer(sender_id: int, receiver_id: int, amount: float, status: str, 
                 transfer_id: Optional[str] = None) -> None:
    """Log balance transfer"""
    log_event(
        "transfer",
        level="info",
        sender_id=sender_id,
        receiver_id=receiver_id,
        amount=amount,
        status=status,
        transfer_id=transfer_id
    )


def log_security_event(event: str, user_id: Optional[int], severity: str, 
                       details: Dict[str, Any]) -> None:
    """Log security-related events"""
    level = "critical" if severity == "high" else "warning"
    log_event(
        "security",
        level=level,
        security_event=event,
        user_id=user_id,
        severity=severity,
        **details
    )

# ==================== PERFORMANCE LOGGING ====================
class PerformanceLogger:
    """Context manager for performance logging"""
    
    def __init__(self, operation: str, **metadata):
        self.operation = operation
        self.metadata = metadata
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        logger.debug(f"Starting {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        duration_ms = (self.end_time - self.start_time) * 1000
        
        if exc_type:
            logger.error(f"{self.operation} failed after {duration_ms:.2f}ms: {exc_val}")
        else:
            log_event(
                "performance",
                level="debug",
                operation=self.operation,
                duration_ms=round(duration_ms, 2),
                **self.metadata
            )
            logger.debug(f"{self.operation} completed in {duration_ms:.2f}ms")
    
    def get_duration_ms(self) -> float:
        """Get current duration in milliseconds"""
        if self.start_time is None:
            return 0
        return (time.perf_counter() - self.start_time) * 1000

# ==================== DECORATORS ====================
def log_function_call(func):
    """Decorator to log function calls with arguments"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Get argument names (for better logging)
        func_name = func.__name__
        arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
        
        # Prepare log data (exclude large objects)
        log_args = {}
        for i, arg in enumerate(args):
            if i < len(arg_names):
                arg_name = arg_names[i]
                if hasattr(arg, '__dict__'):
                    log_args[arg_name] = f"<{type(arg).__name__} object>"
                else:
                    log_args[arg_name] = arg
        
        logger.debug(f"Calling {func_name} with args={log_args}, kwargs={kwargs}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Completed {func_name}")
            return result
        except Exception as e:
            log_error(e, {"function": func_name})
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
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            duration = (time.perf_counter() - start) * 1000
            logger.debug(f"{func.__name__} took {duration:.2f}ms")
            return result
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            logger.error(f"{func.__name__} failed after {duration:.2f}ms: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            duration = (time.perf_counter() - start) * 1000
            logger.debug(f"{func.__name__} took {duration:.2f}ms")
            return result
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            logger.error(f"{func.__name__} failed after {duration:.2f}ms: {e}")
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def log_error_handler(func):
    """Decorator to catch and log errors without crashing"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            log_error(e, {"function": func.__name__})
            return None
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_error(e, {"function": func.__name__})
            return None
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

# ==================== CONTEXT MANAGERS ====================
class RequestLogger:
    """Context manager for logging request processing"""
    
    def __init__(self, request_name: str, user_id: Optional[int] = None):
        self.request_name = request_name
        self.user_id = user_id
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        logger.info(f"Starting {self.request_name}" + (f" for user {self.user_id}" if self.user_id else ""))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.utcnow()
        duration = (self.end_time - self.start_time).total_seconds() * 1000
        
        if exc_type:
            logger.error(f"{self.request_name} failed after {duration:.2f}ms: {exc_val}")
        else:
            log_event(
                "request",
                level="info",
                request=self.request_name,
                user_id=self.user_id,
                duration_ms=round(duration, 2),
                status="success"
            )
            logger.info(f"{self.request_name} completed in {duration:.2f}ms")
    
    def get_duration_ms(self) -> float:
        """Get current duration in milliseconds"""
        if self.start_time is None:
            return 0
        return (datetime.utcnow() - self.start_time).total_seconds() * 1000


class BatchLogger:
    """Context manager for batch operations"""
    
    def __init__(self, batch_name: str, total_items: int):
        self.batch_name = batch_name
        self.total_items = total_items
        self.processed_items = 0
        self.errors = 0
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        logger.info(f"Starting batch {self.batch_name} with {self.total_items} items")
        return self
    
    def item_processed(self, success: bool = True):
        """Mark one item as processed"""
        self.processed_items += 1
        if not success:
            self.errors += 1
        
        # Log progress every 10%
        if self.processed_items % max(1, self.total_items // 10) == 0:
            progress = (self.processed_items / self.total_items) * 100
            logger.info(f"Batch {self.batch_name}: {progress:.0f}% complete ({self.processed_items}/{self.total_items})")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.perf_counter() - self.start_time) * 1000
        status = "completed" if self.errors == 0 else f"completed with {self.errors} errors"
        
        log_event(
            "batch",
            level="info",
            batch=self.batch_name,
            total_items=self.total_items,
            processed=self.processed_items,
            errors=self.errors,
            duration_ms=round(duration, 2),
            status=status
        )
        
        logger.info(f"Batch {self.batch_name} {status} in {duration:.2f}ms")

# ==================== CLEANUP ====================
def cleanup_old_logs(days: int = LOG_RETENTION_DAYS):
    """Delete log files older than specified days"""
    cutoff = datetime.now() - timedelta(days=days)
    deleted_count = 0
    
    for log_file in LOG_DIR.glob("*.log*"):
        if log_file.stat().st_mtime < cutoff.timestamp():
            log_file.unlink()
            deleted_count += 1
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} old log files")
    
    return deleted_count

# ==================== EXPORTS ====================
__all__ = [
    # Logger
    'logger',
    'setup_logger',
    'LogLevel',
    'LogLevelManager',
    
    # Structured logging
    'log_event',
    'log_user_action',
    'log_error',
    'log_api_call',
    'log_database_query',
    'log_bot_command',
    'log_game_event',
    'log_transfer',
    'log_security_event',
    
    # Performance
    'PerformanceLogger',
    'RequestLogger',
    'BatchLogger',
    
    # Decorators
    'log_function_call',
    'log_performance',
    'log_error_handler',
    
    # Cleanup
    'cleanup_old_logs',
    
    # Classes
    'LogEvent',
]

# ==================== INITIAL CLEANUP ====================
if __name__ != "__main__":
    # Run cleanup on module load (but not during tests)
    try:
        cleanup_old_logs()
    except Exception:
        pass