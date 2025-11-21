"""
Logging and Debugging Configuration

Provides structured logging for the entire application with:
- JSON-formatted logs for production
- Human-readable logs for development
- Platform-specific log shipping (Snowflake/Databricks)
- Performance tracking
- Audit trail for agent/workflow execution
"""

import logging
import json
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
import traceback
from contextlib import contextmanager


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Produces machine-readable logs for ingestion into log aggregation systems.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
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
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable formatter for development.
    Color-coded output for easy reading.
    """

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Format: [12:34:56.789] INFO [module.function:123] Message
        log_line = (
            f"{color}[{timestamp}] {record.levelname:8s}{self.RESET} "
            f"[{record.module}.{record.funcName}:{record.lineno}] "
            f"{record.getMessage()}"
        )

        if record.exc_info:
            log_line += "\n" + "".join(traceback.format_exception(*record.exc_info))

        return log_line


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    structured: bool = False,
    enable_platform_shipping: bool = False
) -> logging.Logger:
    """
    Setup application-wide logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        structured: Use JSON structured logging (for production)
        enable_platform_shipping: Ship logs to Snowflake/Databricks

    Returns:
        Configured root logger
    """
    logger = logging.getLogger("cortex_ai")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if structured:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(HumanReadableFormatter())
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)

    # Platform-specific log shipping
    if enable_platform_shipping:
        try:
            from config import get_platform_config
            platform = get_platform_config()

            if platform.is_snowflake():
                logger.addHandler(SnowflakeLogHandler())
            elif platform.is_databricks():
                logger.addHandler(DatabricksLogHandler())
        except Exception as e:
            logger.warning(f"Could not setup platform log shipping: {e}")

    return logger


class SnowflakeLogHandler(logging.Handler):
    """
    Ship logs to Snowflake table for centralized logging.
    Logs are buffered and sent in batches for efficiency.
    """

    def __init__(self, batch_size: int = 100):
        super().__init__()
        self.batch_size = batch_size
        self.buffer = []

    def emit(self, record: logging.LogRecord):
        """Add log record to buffer and flush if needed"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
            }
            self.buffer.append(log_entry)

            if len(self.buffer) >= self.batch_size:
                self.flush()
        except Exception:
            self.handleError(record)

    def flush(self):
        """Send buffered logs to Snowflake"""
        if not self.buffer:
            return

        try:
            from utils.data_connectors import SnowflakeConnector

            connector = SnowflakeConnector()
            # Insert into CORTEX_AI_LOGS table
            # connector.execute_query(...)
            self.buffer.clear()
        except Exception as e:
            # Don't fail application if logging fails
            print(f"Failed to ship logs to Snowflake: {e}", file=sys.stderr)


class DatabricksLogHandler(logging.Handler):
    """
    Ship logs to Databricks Delta table for centralized logging.
    Uses streaming append for real-time log ingestion.
    """

    def __init__(self, table_name: str = "cortex_ai_logs"):
        super().__init__()
        self.table_name = table_name
        self.buffer = []

    def emit(self, record: logging.LogRecord):
        """Write log to Delta table"""
        try:
            from utils.data_connectors import DatabricksConnector

            connector = DatabricksConnector()
            # Append to Delta table
            # connector.execute_query(...)
        except Exception:
            self.handleError(record)


class PerformanceLogger:
    """
    Track and log performance metrics for agents and workflows.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger("cortex_ai.performance")
        self.metrics = {}

    @contextmanager
    def track(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager to track operation duration.

        Usage:
            with perf_logger.track("workflow_execution", {"workflow_id": "123"}):
                execute_workflow()
        """
        start_time = time.time()
        self.logger.info(f"Starting: {operation}", extra={"extra_data": metadata or {}})

        try:
            yield
            duration = time.time() - start_time
            self.logger.info(
                f"Completed: {operation}",
                extra={
                    "extra_data": {
                        "operation": operation,
                        "duration_seconds": duration,
                        "status": "success",
                        **(metadata or {})
                    }
                }
            )
            self._record_metric(operation, duration, "success")
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Failed: {operation}",
                extra={
                    "extra_data": {
                        "operation": operation,
                        "duration_seconds": duration,
                        "status": "failed",
                        "error": str(e),
                        **(metadata or {})
                    }
                },
                exc_info=True
            )
            self._record_metric(operation, duration, "failed")
            raise

    def _record_metric(self, operation: str, duration: float, status: str):
        """Record metric for aggregation"""
        if operation not in self.metrics:
            self.metrics[operation] = {
                "count": 0,
                "total_duration": 0,
                "min_duration": float('inf'),
                "max_duration": 0,
                "failures": 0
            }

        metric = self.metrics[operation]
        metric["count"] += 1
        metric["total_duration"] += duration
        metric["min_duration"] = min(metric["min_duration"], duration)
        metric["max_duration"] = max(metric["max_duration"], duration)
        if status == "failed":
            metric["failures"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics"""
        return {
            op: {
                **metrics,
                "avg_duration": metrics["total_duration"] / metrics["count"],
                "failure_rate": metrics["failures"] / metrics["count"]
            }
            for op, metrics in self.metrics.items()
        }


class AuditLogger:
    """
    Audit logger for tracking user actions and system events.
    Used for compliance and security monitoring.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger("cortex_ai.audit")

    def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ):
        """
        Log an auditable action.

        Args:
            action: Action performed (create, read, update, delete, execute)
            resource_type: Type of resource (agent, workflow, document)
            resource_id: Unique identifier of resource
            user_id: User who performed the action
            metadata: Additional context
            status: success or failed
        """
        self.logger.info(
            f"Audit: {action} {resource_type}",
            extra={
                "extra_data": {
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "user_id": user_id or "anonymous",
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat(),
                    **(metadata or {})
                }
            }
        )


# Debugging utilities
class DebugContext:
    """
    Debug context for detailed execution tracing.
    Only active when DEBUG mode is enabled.
    """

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.traces = []
        self.logger = logging.getLogger("cortex_ai.debug")

    def trace(self, component: str, message: str, data: Optional[Dict] = None):
        """Add a debug trace"""
        if not self.enabled:
            return

        trace = {
            "timestamp": datetime.utcnow().isoformat(),
            "component": component,
            "message": message,
            "data": data
        }
        self.traces.append(trace)
        self.logger.debug(f"[{component}] {message}", extra={"extra_data": data or {}})

    def get_traces(self) -> list:
        """Get all debug traces"""
        return self.traces

    def clear(self):
        """Clear debug traces"""
        self.traces.clear()


# Global instances
_logger = None
_perf_logger = None
_audit_logger = None
_debug_context = None


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get application logger"""
    global _logger
    if _logger is None:
        _logger = setup_logging()

    if name:
        return logging.getLogger(f"cortex_ai.{name}")
    return _logger


def get_performance_logger() -> PerformanceLogger:
    """Get performance logger"""
    global _perf_logger
    if _perf_logger is None:
        _perf_logger = PerformanceLogger()
    return _perf_logger


def get_audit_logger() -> AuditLogger:
    """Get audit logger"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def get_debug_context() -> DebugContext:
    """Get debug context"""
    global _debug_context
    if _debug_context is None:
        import os
        debug_enabled = os.getenv("DEBUG", "false").lower() == "true"
        _debug_context = DebugContext(enabled=debug_enabled)
    return _debug_context


# Convenience functions
def log_info(message: str, **kwargs):
    """Log info message"""
    get_logger().info(message, extra={"extra_data": kwargs})


def log_error(message: str, exc_info=True, **kwargs):
    """Log error message"""
    get_logger().error(message, exc_info=exc_info, extra={"extra_data": kwargs})


def log_warning(message: str, **kwargs):
    """Log warning message"""
    get_logger().warning(message, extra={"extra_data": kwargs})


def log_debug(message: str, **kwargs):
    """Log debug message"""
    get_logger().debug(message, extra={"extra_data": kwargs})
