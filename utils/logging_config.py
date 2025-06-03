"""
Logging Configuration - Production-ready logging setup
Handles structured logging, log rotation, and different output formats
"""

import logging
import logging.handlers
import sys
import json
from datetime import datetime
from typing import Dict, Any
import structlog
from utils.env_utils import get_env_str, is_production, is_development

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "ip_address"):
            log_entry["ip_address"] = record.ip_address
        
        return json.dumps(log_entry, ensure_ascii=False)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for development logging"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        if not is_development():
            return super().format(record)
        
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format: [TIMESTAMP] LEVEL LOGGER: MESSAGE
        formatted = f"{color}[{datetime.now().strftime('%H:%M:%S')}] {record.levelname} {record.name}: {record.getMessage()}{reset}"
        
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted

def setup_logging():
    """Setup application logging configuration"""
    
    # Environment variables
    LOG_LEVEL = get_env_str("LOG_LEVEL", "INFO")
    LOG_FORMAT = get_env_str("LOG_FORMAT", "json")
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set log level
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Choose formatter based on environment and format setting
    if LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        if is_development():
            formatter = ColoredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for production
    if is_production():
        # Create logs directory if it doesn't exist
        import os
        os.makedirs("logs", exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            "logs/app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            "logs/error.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(error_handler)
    
    # Configure specific loggers
    configure_loggers()
    
    # Setup structlog
    setup_structlog()

def configure_loggers():
    """Configure specific logger levels"""
    DEBUG = get_env_str("DEBUG", "false").lower() == "true"
    
    loggers_config = {
        "uvicorn": logging.INFO,
        "uvicorn.access": logging.INFO if DEBUG else logging.WARNING,
        "sqlalchemy.engine": logging.WARNING,
        "sqlalchemy.pool": logging.WARNING,
        "alembic": logging.INFO,
        "httpx": logging.WARNING,
        "google.generativeai": logging.WARNING,
    }
    
    for logger_name, level in loggers_config.items():
        logging.getLogger(logger_name).setLevel(level)

def setup_structlog():
    """Setup structlog for structured logging"""
    LOG_FORMAT = get_env_str("LOG_FORMAT", "json")
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

class LoggerMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self):
        """Get logger instance for the class"""
        if not hasattr(self, '_logger'):
            self._logger = structlog.get_logger(self.__class__.__name__)
        return self._logger

def get_logger(name: str = None):
    """Get a logger instance"""
    return structlog.get_logger(name)

def log_request(request_id: str, method: str, path: str, user_id: int = None, ip_address: str = None):
    """Log HTTP request"""
    logger = get_logger("request")
    logger.info(
        "HTTP request",
        request_id=request_id,
        method=method,
        path=path,
        user_id=user_id,
        ip_address=ip_address
    )

def log_response(request_id: str, status_code: int, response_time: float):
    """Log HTTP response"""
    logger = get_logger("response")
    logger.info(
        "HTTP response",
        request_id=request_id,
        status_code=status_code,
        response_time_ms=round(response_time * 1000, 2)
    )

def log_error(error: Exception, context: Dict[str, Any] = None):
    """Log error with context"""
    logger = get_logger("error")
    logger.error(
        "Application error",
        error=str(error),
        error_type=type(error).__name__,
        context=context or {},
        exc_info=True
    )

def log_security_event(event_type: str, user_id: int = None, ip_address: str = None, details: Dict[str, Any] = None):
    """Log security-related events"""
    logger = get_logger("security")
    logger.warning(
        "Security event",
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        details=details or {}
    )

def log_database_operation(operation: str, table: str, duration: float = None, affected_rows: int = None):
    """Log database operations"""
    logger = get_logger("database")
    logger.debug(
        "Database operation",
        operation=operation,
        table=table,
        duration_ms=round(duration * 1000, 2) if duration else None,
        affected_rows=affected_rows
    )

# Initialize logging when module is imported
setup_logging() 